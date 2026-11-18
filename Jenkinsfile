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

        stage('Deploy to Render') {
            when {
                expression {
                    env.BRANCH_NAME == 'main' ||
                    env.GIT_BRANCH == 'origin/main' ||
                    env.GIT_BRANCH == 'main'
                }
            }
            steps {
                withCredentials([string(credentialsId: 'render-deploy-hook', variable: 'RENDER_DEPLOY_HOOK')]) {
                    bat 'curl.exe --fail --silent --show-error -X POST "%RENDER_DEPLOY_HOOK%"'
                }
            }
        }
    }

    post {
        success {
            echo 'All tests passed and deployment was triggered.'
        }
        failure {
            echo 'Pipeline failed. Deployment was not triggered.'
        }
    }
}

