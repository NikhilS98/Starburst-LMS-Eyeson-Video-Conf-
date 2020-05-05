from sqlalchemy import text

from Application import app, org
from Application import models
from flask import request, render_template, redirect, flash, session, send_file
from Application.decorators.authenticate import authenticate
from datetime import datetime
from werkzeug.utils import secure_filename
from markupsafe import escape
import os

ASSIGNMENT_UPLOAD_FOLDER = 'assignments'
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

    print(submissions)
    return render_template('assignment_submission.html', submissions=submissions,
                           enrollmentRole=enrollmentRole)

@app.route('/downloadSubmission')
@authenticate
def downloadSubmission():
    # logic for downloading

    # after successful download
    return redirect('assignmentSubmission')

@app.route('/submitAssignment/<id>', methods=["GET", "POST"])
@authenticate
def submit_assignment(id):
    if request.method == "GET":
        return render_template('submit_assignment_modal.html')
    # logic for submission
    formData = request.form

    submission = models.AssignmentSubmission()
    submission.assignmentId = escape(id)
    submission.userId = session["id"]
    submission.submissionTime = datetime.datetime.today()

    files = request.files.getlist("files")

    # this is needed to create dir if it doesn't exist, otherwise file.save fails.
    submissionDir = os.path.join(PROJECT_DIR, ASSIGNMENT_UPLOAD_FOLDER)
    if not os.path.exists(submissionDir):
        os.makedirs(submissionDir)

    # for file in files:
    #     # for some reason when not uploading any file it was still reaching this code
    #     # with an empty file so I included this check for now
    #     if file:
    #         path = os.path.join(assignmentDir, secure_filename(file.filename))
    #         file.save(path)
    #         newAssignmentFile = models.AssignmentFile()
    #         newAssignmentFile.filePath = path
    #
    #         newAssignment.assignmentFiles.append(newAssignmentFile)

    models.db.session.add(submission)
    models.db.session.commit()

    # after successful submission
    flash("Assignment Submitted")
    return redirect('assignmentSubmission')