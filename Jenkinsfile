pipeline {
    agent any

    environment {
        // Defines the Python executable to use
        PYTHON = 'python3'
    }

    stages {
        stage('Checkout') {
            steps {
                // Jenkins automatically checks out the repository. 
                // We're just logging that we are starting the pipeline.
                echo 'Checking out source code...'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                dir('outputs/backend') {
                    echo 'Installing Python dependencies...'
                    // Setting up a virtual environment is best practice
                    bat '''
                        $PYTHON -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Linting or Checking') {
            steps {
                dir('outputs/backend') {
                    echo 'Running Python Linting/Checks...'
                    bat '''
                        . venv/bin/activate
                        # You can add flake8 or pylint here to check the code quality:
                        # pip install flake8
                        # flake8 .
                        echo "Skipping linting since it's not configured yet."
                    '''
                }
            }
        }

        stage('Test') {
            steps {
                dir('outputs/backend') {
                    echo 'Running Unit Tests...'
                    bat '''
                        . venv/bin/activate
                        # Add your pytest setup here when tests are available:
                        # pip install pytest
                        # pytest
                        echo "No tests found. Skipping tests."
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                dir('outputs/backend') {
                    echo 'Deploying AI Conversation Studio...'
                    // Add your deployment commands here (e.g. dockerize, pubat to aws/azure, etc.)
                   echo 'Deployment complete. The app can be run locally using: uvicorn main:app --reload --port 8000'
                }
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline has completed.'
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed! Please check the logs.'
        }
    }
}
