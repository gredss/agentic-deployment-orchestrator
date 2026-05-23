from flask import Flask, request, jsonify
import requests
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JENKINS_URL = os.getenv('JENKINS_URL', 'https://jenkins-production.apps.itz-gkg33y.infra01-lb.tok04.techzone.ibm.com')
JENKINS_USER = os.getenv('JENKINS_USER', 'admin')
JENKINS_TOKEN = os.getenv('JENKINS_TOKEN', '11a65eafe8d68c1e7d44f29f32859739c4')
JENKINS_JOB = os.getenv('JENKINS_JOB', 'python-app-deployment')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "bob-orchestrator"})

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    text = data.get('text', '').lower()
    
    if 'deploy' in text and 'production' in text:
        result = trigger_jenkins_deployment()
        return jsonify(result)
    
    return jsonify({"status": "ignored", "message": "No deployment command detected"})

def trigger_jenkins_deployment():
    try:
        url = f"{JENKINS_URL}/job/{JENKINS_JOB}/build"
        auth = (JENKINS_USER, JENKINS_TOKEN)
        
        logger.info(f"Triggering Jenkins job: {JENKINS_JOB}")
        response = requests.post(url, auth=auth, verify=False)
        
        if response.status_code in [200, 201]:
            return {
                "status": "success",
                "message": f"Deployment triggered for {JENKINS_JOB}",
                "jenkins_url": f"{JENKINS_URL}/job/{JENKINS_JOB}"
            }
        else:
            return {
                "status": "error",
                "message": f"Jenkins returned {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        logger.error(f"Error triggering Jenkins: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# Made with Bob
