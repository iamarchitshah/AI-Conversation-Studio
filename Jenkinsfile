pipeline {
    agent any

    environment {
        // Defines the Python executable to use
        PYTHON = 'python'
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
                        %PYTHON% -m venv venv
                        call venv\\Scripts\\activate.bat
                        python -m pip install --upgrade pip
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
                        call venv\\Scripts\\activate.bat
                        REM You can add flake8 or pylint here to check the code quality:
                        REM pip install flake8
                        REM flake8 .
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
                        call venv\\Scripts\\activate.bat
                        REM Add your pytest setup here when tests are available:
                        REM pip install pytest
                        REM pytest
                        echo "No tests found. Skipping tests."
                    '''
                }
            }
        }
        
        stage('Deploy to AWS EKS') {
            environment {
                // Configuration for AWS EKS deployment
                AWS_ACCOUNT_ID = '419676625590'
                AWS_REGION = 'us-east-1'
                CLUSTER_NAME = 'ai-conversation-studio-cluster'
                ECR_REPO = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/ai-conversation-studio"
            }
            steps {
                // Return to workspace root because Dockerfile and k8s/ are in the root directory
                dir('.') {
                    echo '1. Authenticating with AWS ECR...'
                    bat "aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REPO%"
                    
                    echo '2. Building the Docker Image...'
                    bat "docker build -t ai-conversation-studio:latest ."
                    
                    echo '3. Tagging and Pushing Image to ECR...'
                    bat "docker tag ai-conversation-studio:latest %ECR_REPO%:latest"
                    bat "docker push %ECR_REPO%:latest"
                    
                    echo '4. Updating Kubeconfig for EKS...'
                    bat "aws eks update-kubeconfig --region %AWS_REGION% --name %CLUSTER_NAME%"
                    
                    echo '5. Applying Kubernetes Manifests...'
                    bat "kubectl apply -f k8s/"
                    
                    echo 'Deployment complete!'
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
