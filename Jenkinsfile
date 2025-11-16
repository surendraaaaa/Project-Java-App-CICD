pipeline {
    agent any
    environment {
        SCANNER_HOME= tool 'sonar-scanner'
        SONAR_HOST_URL = "http://3.12.196.109:9000"
        }
    stages {

        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Git Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/surendraaaaa/Project-Java-App-CICD.git'
            }
        }

        stage('Maven Validate') {
            steps {
                dir('legacy-java-app') {
                    sh 'mvn validate'
                }
            }
        }

        stage('Maven Compile') {
            steps {
                dir('legacy-java-app') {
                    sh 'mvn compile'
                }
            }
        }

        stage('Maven Package') {
            steps {
                dir('legacy-java-app') {
                    sh 'mvn package'
                }
            }
        }

        stage('Maven Install') {
            steps {
                dir('legacy-java-app') {
                    sh 'mvn clean install -DskipTests'
                }
            }
            post {
                success {
                    archiveArtifacts artifacts: 'legacy-java-app/target/*.jar', fingerprint: true
                }
            }
        }

        stage('Trivy FS Scan') {
            steps {
                sh "trivy fs --format table -o fs-report.html ."
            }
            post {
                always {
                    archiveArtifacts artifacts: 'fs-report.html', fingerprint: true
                }
            }
        }
        
        stage('GitLeaks Secret Scan') {
            steps {
                sh '''
                gitleaks detect --source . --report-path gitleaks-report.json --report-format json --verbose
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'gitleaks-report.json', fingerprint: true
                }
                failure {
                    error("Gitleaks detected secrets! Pipeline failed.")
                }
            }
        }



        stage('Sonar Scan') {
            steps {
                dir('legacy-java-app') {
                    withSonarQubeEnv('sonar') {
                        // sh " $SCANNER_HOME/bin/sonar-scanner -Dsonar.projectKey=devops -Dsonar.projectName=devops"
                        sh """
                        $SCANNER_HOME/bin/sonar-scanner \
                        -Dsonar.projectKey=devops \
                        -Dsonar.projectName=devops \
                        -Dsonar.sources=src/main/java \
                        -Dsonar.java.binaries=target/classes
                         """
                    }
                }
            }
        }
        
        stage('Upload Artifact & Reports to S3') {
             steps {
        withAWS(credentials: 'aws-cred', region: 'us-east-2') {
            // Inject your custom Sonar token here
            withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                sh '''
                aws s3 cp legacy-java-app/target/legacy-java-app-1.0.0.jar s3://project1-javaapp-artifact-bucket/artifacts/
                aws s3 cp fs-report.html s3://project1-javaapp-artifact-bucket/trivy/
                aws s3 cp gitleaks-report.json s3://project1-javaapp-artifact-bucket/gitleaks/

                # Use the injected variable SONAR_TOKEN
                curl -u "${SONAR_TOKEN}:" "${SONAR_HOST_URL}/api/issues/search?componentKeys=devops" -o sonar-report.json

                aws s3 cp sonar-report.json s3://project1-javaapp-artifact-bucket/sonar/
                '''
            }
        }
    }
}
        stage('Approval: Deploy to EC2') 
            { steps 
                { timeout(time: 10, unit: 'MINUTES')
                { input message: "Proceed with deployment to EC2?" } 
                } 
            }
            
        stage('Deploy to EC2 via Ansible') {
            steps {
                withAWS(credentials: 'aws-cred', region: 'us-east-2') {
                    withEnv(["ANSIBLE_HOST_KEY_CHECKING=False"]) {
                        dir("${WORKSPACE}/ansible") {
                            sh '''
                            ansible-playbook -i inventories/prod/ec2.py playbooks/deploy.yml
                            '''
                        }
                    }
                }
            }
        }


}
    
        
        post {
        success {
        emailext(
            subject: "SUCCESS: Jenkins Pipeline '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
            to: "ashukumavat555@gmail.com",
            mimeType: 'text/html',
            body: """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #f6f6f6; color: #333; }
                    .container { max-width: 600px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);}
                    .header { text-align: center; }
                    .header h2 { color: #4CAF50; }
                    .details { margin-top: 20px; }
                    .details table { width: 100%; border-collapse: collapse; }
                    .details th, .details td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
                    .footer { margin-top: 30px; font-size: 12px; color: #888; text-align: center; }
                    a.button { background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
                    a.button:hover { background-color: #45a049; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Pipeline Success</h2>
                        <p><strong>${env.JOB_NAME} [#${env.BUILD_NUMBER}]</strong></p>
                    </div>
                    <div class="details">
                        <table>
                            <tr>
                                <th>Status</th>
                                <td style="color: #4CAF50;"><strong>SUCCESS</strong></td>
                            </tr>
                            <tr>
                                <th>Build URL</th>
                                <td><a class="button" href="${env.BUILD_URL}">View Build</a></td>
                            </tr>
                            <tr>
                                <th>Triggered By</th>
                                <td>${currentBuild.getBuildCauses('hudson.model.Cause$UserIdCause')[0]?.userName ?: 'Automated'}</td>
                            </tr>
                            <tr>
                                <th>Start Time</th>
                                <td>${new Date(currentBuild.startTimeInMillis).format('yyyy-MM-dd HH:mm:ss')}</td>
                            </tr>
                            <tr>
                                <th>End Time</th>
                                <td>${new Date().format('yyyy-MM-dd HH:mm:ss')}</td>
                            </tr>
                        </table>
                    </div>
                    <div class="footer">
                        <p>This is an automated notification from Jenkins CI/CD system.</p>
                    </div>
                </div>
            </body>
            </html>
            """

        )
    }
}

        
    
}
