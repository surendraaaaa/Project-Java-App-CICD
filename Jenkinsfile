pipeline {
    agent any

    parameters {
        choice(name: 'ENV', choices: ['dev', 'staging', 'prod'], description: 'Choose Environment to Deploy')
        booleanParam(name: 'ROLLBACK', defaultValue: false, description: 'Enable rollback instead of new deployment?')
        string(name: 'ROLLBACK_VERSION', defaultValue: '', description: 'Provide version (Build Number) to rollback to')
        text(name: 'EC2_REGIONS', defaultValue: 'us-east-1,us-east-2', description: 'Comma-separated list of EC2 regions to deploy to')
        choice(name: 'S3_REGION', choices: ['us-east-1', 'us-east-2', 'us-west-1', 'eu-west-1'], description: 'Region of S3 bucket')
    }

    environment {
        SCANNER_HOME = tool 'sonar-scanner'
        SONAR_HOST_URL = "http://3.150.125.216:9000"
    }

    stages {

        stage('Clean Workspace') {
            when { expression { return !params.ROLLBACK } }
            steps { cleanWs() }
        }

        stage('Git Checkout') {
            when { expression { return !params.ROLLBACK } }
            steps { git branch: 'feature', url: 'https://github.com/surendraaaaa/Project-Java-App-CICD.git' }
        }

        stage('Maven Build & Package') {
            when { expression { return !params.ROLLBACK } }
            steps {
                dir('legacy-java-app') {
                    sh "mvn clean package -DskipTests -Dbuild.number=${BUILD_NUMBER}"
                }
            }
            post {
                success {
                    archiveArtifacts artifacts: 'legacy-java-app/target/*.jar', fingerprint: true
                }
            }
        }

        stage('Trivy FS Scan') {
            when { expression { return !params.ROLLBACK } }
            steps {
                sh "trivy fs --format table -o fs-report-${BUILD_NUMBER}.html ."
            }
            post { always { archiveArtifacts artifacts: "fs-report-${BUILD_NUMBER}.html" } }
        }

        stage('Gitleaks Scan') {
            when { expression { return !params.ROLLBACK } }
            steps {
                sh "gitleaks detect --source . --report-path gitleaks-report-${BUILD_NUMBER}.json --report-format json --verbose || true"
            }
            post { always { archiveArtifacts artifacts: "gitleaks-report-${BUILD_NUMBER}.json" } }
        }

        stage('Sonar Scan') {
            when { expression { return !params.ROLLBACK } }
            steps {
                dir('legacy-java-app') {
                    withSonarQubeEnv('sonar') {
                        sh """
                        $SCANNER_HOME/bin/sonar-scanner \
                        -Dsonar.projectKey=devops \
                        -Dsonar.sources=src/main/java \
                        -Dsonar.java.binaries=target/classes
                        """
                    }
                }
            }
        }

        stage('Upload Artifact & Reports to S3') {
            when { expression { return !params.ROLLBACK } }
            steps {
                script {
                    // Dynamically set S3 bucket based on selected region
                    env.S3_BUCKET = "project1-javaapp-bucket-${params.S3_REGION}"
                }

                withAWS(credentials: 'aws-cred', region: params.S3_REGION) {
                    sh """
                    # Upload artifact
                    aws s3 cp legacy-java-app/target/*.jar \
                    s3://${S3_BUCKET}/artifacts/build-${BUILD_NUMBER}.jar

                    # Upload Trivy report
                    aws s3 cp fs-report-${BUILD_NUMBER}.html \
                    s3://${S3_BUCKET}/reports/fs-report-${BUILD_NUMBER}.html

                    # Upload Gitleaks report
                    aws s3 cp gitleaks-report-${BUILD_NUMBER}.json \
                    s3://${S3_BUCKET}/reports/gitleaks-report-${BUILD_NUMBER}.json
                    """
                }
            }
        }

        stage('Approval Before Deployment') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        if (params.ROLLBACK && !params.ROLLBACK_VERSION) {
                                error "ROLLBACK_VERSION must be provided when ROLLBACK is enabled"
                            }
                        if (!params.ROLLBACK) {
                            input "Deploy Build #${BUILD_NUMBER} to ${params.ENV}?"
                        } else {
                            input "Perform rollback of build #${params.ROLLBACK_VERSION} to ${params.ENV}?"
                        }
                    }
                }
            }
        }

        stage('Deploy via Ansible to Multiple Regions') {
            steps {
                script {
                    def ec2Regions = params.EC2_REGIONS
                        .split(',')
                        .collect { it.trim() }
                        .findAll { it }  // removes empty regions
                    for (region in ec2Regions) {
                        stage("Deploy to EC2 in ${region.trim()}") {
                            withAWS(credentials: 'aws-cred', region: region.trim()) {
                                withEnv(["AWS_REGION=${region.trim()}", "ANSIBLE_HOST_KEY_CHECKING=False"]) {
                                    dir("${WORKSPACE}/ansible") {
                                        sh """
                                        chmod +x inventories/${params.ENV}/ec2.py
                                        ansible-playbook -i inventories/${params.ENV}/ec2.py playbooks/deploy.yml \
                                        --extra-vars "artifact_version=${params.ROLLBACK ? params.ROLLBACK_VERSION : BUILD_NUMBER} env=${params.ENV} aws_region=${region.trim()}"
                                        """
                                    }
                                }
                            }
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
