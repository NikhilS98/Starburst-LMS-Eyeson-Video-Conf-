from sqlalchemy import text

from Application import app, org
from Application import models
from flask import request, render_template, redirect, flash, session, send_file, url_for
from Application.decorators.authenticate import authenticate
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from markupsafe import escape
import os

ASSIGNMENT_SUBMISSION_FOLDER = 'assignments/{}/submissions'
PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files', str(org.orgId))

@app.route('/assignmentSubmission/<id>')
@authenticate
def assignmentSubmission(id):
    assignmentId = escape(id)

    # this doesn't give the desired out but leaving here for reference if
    # needed to execute raw sql again
    # sql = text('select enrollmentRole from enrollments e '
    #           'inner join courses c on e.courseId = c.courseId '
    #           'inner join assignments a on a.courseId = c.courseId '
    #           'where a.assignmentId = :id')
    # enrollmentType = models.db.engine.execute(sql, id=3).fetchall()
    # print(enrollmentType)

    # to get the enrollmentRole. This is very inefficient i think
    # but gets the job done for now
    result = models.Assignment.query.filter_by(assignmentId=assignmentId).first()
    enrollments = result.course.enrollments
    enrollmentRole = [e for e in enrollments if e.userId == session['id']][0].enrollmentRole
    print(enrollmentRole)

    isTeacher = (enrollmentRole == models.EnrollmentRole.Teacher)

    submissions = []

    if enrollmentRole == models.EnrollmentRole.Teacher:
        submissions = models.db.session.query(models.AssignmentSubmission)\
            .filter(models.AssignmentSubmission.assignmentId == assignmentId)\
            .all()
    else:
        submissions = models.db.session.query(models.AssignmentSubmission) \
            .filter(models.AssignmentSubmission.assignmentId == assignmentId) \
            .filter(models.AssignmentSubmission.userId == session['id']) \
            .all()

    return render_template('assignment_submission.html', submissions=submissions,
                           enrollmentRole=enrollmentRole, isTeacher=isTeacher, assignmentId=id)

@app.route('/downloadSubmission/<id>')
@authenticate
def downloadSubmission(id):
    submissionFileId = escape(id)

    submissionFile = models.SubmissionFile.query.filter_by(submissionFileId=submissionFileId).first()
    if not submissionFile:
        flash('No file found')
    else:
        return send_file(submissionFile.filePath, as_attachment=True)
    return redirect('assignmentSubmission')

@app.route('/submitAssignment/<id>', methods=["GET", "POST"])
@authenticate
def submitAssignment(id):
    if request.method == "GET":
        return render_template('submit_assignment_page.html', id=id)
    # logic for submission
    formData = request.form

    assignment = models.Assignment.query.filter_by(assignmentId=escape(id)).first()
    if datetime.utcnow() + timedelta(hours=5) > assignment.assignmentDeadline:
        flash('Assignment deadline has passed')
        return render_template('assignment_detail.html', assignment=assignment,
                               isTeacher=session['isTeacher'], hasDeadlinePassed=True)

    submission = models.AssignmentSubmission()
    submission.assignmentId = escape(id)
    submission.userId = session["id"]
    submission.comment = formData["comment"]
    submission.submissionTime = datetime.utcnow() + timedelta(hours=5)

    models.db.session.add(submission)
    models.db.session.flush()

    files = request.files.getlist("files")

    # this is needed to create dir if it doesn't exist, otherwise file.save fails.
    submissionDir = os.path.join(PROJECT_DIR, ASSIGNMENT_SUBMISSION_FOLDER.format(str(submission.assignmentId)),
                                 str(submission.assignmentSubmissionId))

    for file in files:
        if file:
            if not os.path.exists(submissionDir):
                os.makedirs(submissionDir)
            path = os.path.join(submissionDir, secure_filename(file.filename))
            file.save(path)
            submissionFile = models.SubmissionFile()
            submissionFile.filePath = path
            submissionFile.fileName = file.filename
            submissionFile.submissionId = submission.assignmentSubmissionId

            models.db.session.add(submissionFile)
        else:
            flash("No file selected")
            return redirect(url_for('submitAssignment', id=id))

    models.db.session.commit()

    # after successful submission
    flash("Assignment Submitted")
    return redirect(url_for('submitAssignment', id=id))


@app.route('/gradeAssignmentSubmission/<id>', methods=['GET', 'POST'])
@authenticate
def gradeAssignmentSubmission(id):
    if request.method == "GET":
        return render_template('grade_assignment_page.html',id=id)

    result = models.AssignmentSubmission.query.filter_by(assignmentSubmissionId=id).first()
    if not result:
        flash('Assignment Submission does not exist')
        return redirect(url_for('submitAssignment',id=id))

    formData = request.form
    print(formData)
    if 'assignmentGrade' not in formData:
        flash('Please send grade')
        return render_template('grade_assignment_page.html',id=id)

    grade = formData['assignmentGrade']


    result.assignmentGrade = grade
    models.db.session.add(result)
    models.db.session.commit()

    flash('Graded Assignment')
    return redirect(url_for('assignmentSubmissionDetail',id=id))

@app.route('/assignmentSubmission/detail/<id>')
@authenticate
def assignmentSubmissionDetail(id):
    print(id)
    assignmentSubmissionId = escape(id)
    submission = models.AssignmentSubmission.query.filter_by(assignmentSubmissionId=assignmentSubmissionId).first()
    isTeacher = models.Enrollment.query.filter_by(courseId=submission.assignment.courseId, userId=session[
        'id']).first().enrollmentRole == models.EnrollmentRole.Teacher
    return render_template('assignment_submission_detail.html',submission=submission,isTeacher=isTeacher)



