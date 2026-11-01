
pipeline {
    agent any

    environment {
        PYTHON = 'python'
    }

    stages {

        // 1. CHECKOUT FROM GITLAB
        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitLab...'
                checkout scm
            }
        }

        // 2. INSTALL PYTHON DEPENDENCIES
        stage('Install Dependencies') {
            steps {
                dir('outputs/backend') {
                    echo 'Installing Python dependencies...'

                    bat '''
                        %PYTHON% -m venv venv
                        call venv\\Scripts\\activate.bat
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }

        // 3. LINTING
        stage('Linting or Checking') {
            steps {
                dir('outputs/backend') {
                    echo 'Running Python Linting/Checks...'

                    bat '''
                        call venv\\Scripts\\activate.bat

                        REM Add flake8 or pylint when configured.
                        REM pip install flake8
                        REM flake8 .

                        echo Skipping linting since it is not configured yet.
                    '''
                }
            }
        }

        // 4. UNIT TESTING
        stage('Test') {
            steps {
                dir('outputs/backend') {
                    echo 'Running Unit Tests...'

                    bat '''
                        call venv\\Scripts\\activate.bat

                        REM Add pytest when tests are available.
                        REM pip install pytest
                        REM pytest

                        echo No tests found. Skipping tests.
                    '''
                }
            }
        }

        // 5. OWASP ZAP SECURITY SCANNING
        stage('OWASP ZAP Security Scan') {
            steps {
                echo 'Starting OWASP ZAP Security Scan...'

                bat '''
                    docker pull ghcr.io/zaproxy/zaproxy:stable

                    if not exist reports mkdir reports

                    docker run --rm ^
                      -v "%CD%:/zap/wrk/:rw" ^
                      ghcr.io/zaproxy/zaproxy:stable ^
                      zap-baseline.py ^
                      -t http://host.docker.internal:8000 ^
                      -r reports/zap-report.html ^
                      -J reports/zap-report.json ^
                      -I

                    if errorlevel 2 exit /b %ERRORLEVEL%
                '''
            }

            post {
                always {
                    archiveArtifacts(
                        artifacts: 'reports/zap-report.html,reports/zap-report.json',
                        allowEmptyArchive: true
                    )
                }
            }
        }

        // 6. AWS ECR AND EKS CONFIGURATION
        stage('AWS Configuration') {

            environment {
                AWS_ACCOUNT_ID = '419676625590'
                AWS_REGION = 'us-east-1'
                CLUSTER_NAME = 'ai-conversation-studio-cluster'

                ECR_REPO = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/ai-conversation-studio"

                USERPROFILE = 'C:\\Users\\Archit Shah'

                DOCKER_HOST = 'tcp://localhost:2375'
            }

            steps {

                echo 'Checking AWS identity...'

                bat '''
                    aws sts get-caller-identity
                '''

                echo 'Updating EKS kubeconfig...'

                bat '''
                    aws eks update-kubeconfig --region %AWS_REGION% --name %CLUSTER_NAME%
                '''

                echo 'Checking Kubernetes context...'

                bat '''
                    kubectl config current-context
                '''

                echo 'Checking EKS cluster nodes...'

                bat '''
                    kubectl get nodes
                '''
            }
        }

        // 7. AUTHENTICATE WITH AWS ECR
        stage('AWS ECR Authentication') {

            environment {
                AWS_ACCOUNT_ID = '419676625590'
                AWS_REGION = 'us-east-1'
                ECR_REPO = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/ai-conversation-studio"
            }

            steps {

                echo 'Authenticating with AWS ECR...'

                bat '''
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
                '''
            }
        }

        // 8. BUILD DOCKER IMAGE
        stage('Build Docker Image') {
            steps {

                echo 'Building AI Conversation Studio Docker image...'

                bat '''
                    docker build -t ai-conversation-studio:latest .
                '''
            }
        }

        // 9. PUSH IMAGE TO AWS ECR
        stage('Push Docker Image to ECR') {

            environment {
                AWS_ACCOUNT_ID = '419676625590'
                AWS_REGION = 'us-east-1'
                ECR_REPO = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/ai-conversation-studio"
            }

            steps {

                echo 'Tagging Docker image...'

                bat '''
                    docker tag ai-conversation-studio:latest %ECR_REPO%:latest
                '''

                echo 'Pushing Docker image to AWS ECR...'

                bat '''
                    docker push %ECR_REPO%:latest
                '''
            }
        }

        // 10. DEPLOY TO AWS EKS
        stage('Deploy to AWS EKS') {

            environment {
                AWS_REGION = 'us-east-1'
                CLUSTER_NAME = 'ai-conversation-studio-cluster'
            }

            steps {

                echo 'Applying Kubernetes namespace...'

                bat '''
                    kubectl apply -f k8s/namespace.yaml
                '''

                echo 'Applying Kubernetes manifests...'

                bat '''
                    kubectl apply -f k8s/
                '''

                echo 'Checking Kubernetes deployment...'

                bat '''
                    kubectl get deployments -A
                '''

                echo 'Checking Kubernetes pods...'

                bat '''
                    kubectl get pods -A
                '''

                echo 'AWS EKS deployment completed!'
            }
        }
    }

    // POST BUILD ACTIONS
    post {

        always {
            echo 'Pipeline execution completed.'
        }

        success {
            echo 'SUCCESS: CI/CD and security scanning pipeline completed!'
            echo 'OWASP ZAP security reports are available in Jenkins artifacts.'
        }

        failure {
            echo 'FAILURE: Pipeline execution failed.'
            echo 'Please check Jenkins Console Output for details.'
        }
    }
}
