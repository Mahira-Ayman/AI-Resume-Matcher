from flask import Flask,request,render_template,jsonify
import os
from werkzeug.utils import secure_filename
from resume_parser import parse_resume
from matcher import ResumeJobMatcher

app=Flask(__name__)
app.config['UPLOAD_FOLDER']='uploads'
app.config['MAX_CONTENT_LENGTH']=16*1024*1024

os.makedirs(app.config['UPLOAD_FOLDER'],exist_ok=True)

matcher=ResumeJobMatcher()

@app.route('/')
def index():
    return render_template('index.html')

# Helper function to convert numpy types to native Python types
def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif hasattr(obj, "item"):  # e.g., numpy.float32, numpy.int64
        return obj.item()
    return obj


@app.route('/upload',methods=['POST'])
def upload_resume():
    try:
        if "resume" not in request.files:
            return jsonify({'error':'no resume file uploaded'})
        
        file=request.files['resume']
        job_description=request.form.get('job_description', '')

        if file.filename=='':
            return jsonify({'error': 'no file selected'})
        
        if job_description.strip()=='':
            return jsonify({'error':'job description required'})
        
        filename=secure_filename(file.filename)
        filepath=os.path.join(app.config['UPLOAD_FOLDER'],filename)
        file.save(filepath)

        resume_data=parse_resume(filepath)

        if 'error' in resume_data:
            return jsonify(resume_data)

        match_result=matcher.calculate_overall_match(resume_data,job_description)

        os.remove(filepath)
        match_result = convert_numpy_types(match_result)
        return jsonify({
            "success":True,
            "match_result":match_result,
            "resume_info":{
                "email":resume_data['email'],
                "phone":resume_data['phone'],
                "text_length":resume_data['text_length']
            }
        })
    
    except Exception as e:
        return jsonify({'error':f'An error occured:{str(e)}'})
    
if __name__ == '__main__':
    print('Starting Resume Matcher Application...')
    app.run(debug=True)
        