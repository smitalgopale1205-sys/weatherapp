
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    environment {
        VENV = '.venv'
        PYTHON = 'C:\\Program Files\\Python310\\python.exe'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                bat '"%PYTHON%" --version'
                bat '"%PYTHON%" -m venv "%VENV%"'
                bat '"%VENV%\\Scripts\\python.exe" -m pip install --upgrade pip'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '"%VENV%\\Scripts\\python.exe" -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                bat '"%VENV%\\Scripts\\python.exe" -m pytest -v --junitxml=test-results.xml'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }
    }

    post {
        success {
            echo 'All tests passed successfully. Streamlit Community Cloud handles deployment from GitHub.'
        }
        failure {
            echo 'Pipeline failed. Please check the test results and console output.'
        }
    }
}
