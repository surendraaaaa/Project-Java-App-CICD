pipeline {
    agent any

    parameters {
        choice(name: 'ENV', choices: ['dev', 'staging', 'prod'], description: 'Choose Environment to Deploy')
        booleanParam(name: 'ROLLBACK', defaultValue: false, description: 'Enable rollback instead of new deployment?')
        string(name: 'ROLLBACK_VERSION', defaultValue: '', description: 'Provide version (Build Number) to rollback to')
        choice(name: 'REGION', choices: ['us-east-1', 'us-east-2', 'us-west-1', 'eu-west-1'], description: 'Choose AWS Region')
    }

    environment {
        SCANNER_HOME = tool 'sonar-scanner'
        SONAR_HOST_URL = "http://3.12.196.109:9000"
        
        
    }

    stages {

        stage('Clean Workspace') {
            when { expression { return !params.ROLLBACK } }
            steps { cleanWs() }
        }

        stage('Git Checkout') {
            when { expression { return !params.ROLLBACK } }
            steps { git branch: 'main', url: 'https://github.com/surendraaaaa/Project-Java-App-CICD.git' }
        }

        stage('Maven Build & Package') {
            when { expression { return !params.ROLLBACK } }
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

        stage('Security Scans') {
            when { expression { return !params.ROLLBACK } }
            steps {
                sh "trivy fs --format table -o fs-report.html ."
                sh "gitleaks detect --source . --report-path gitleaks-report.json --report-format json --verbose"
            }
            post {
                always {
                    archiveArtifacts artifacts: 'fs-report.html'
                    archiveArtifacts artifacts: 'gitleaks-report.json'
                }
            }
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
                    // Generate S3 bucket dynamically based on selected region
                    env.S3_BUCKET = "project1-javaapp-bucket-${params.REGION}"
                }

                withAWS(credentials: 'aws-cred', region: params.REGION) {
                    sh """
                    aws s3 cp legacy-java-app/target/legacy-java-app-1.0.0.jar \
                    s3://${S3_BUCKET}/artifacts/build-${BUILD_NUMBER}.jar
                    """
                }
            }
        }


        stage('Approval Before Deployment') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        if (!params.ROLLBACK) {
                            input "Deploy Build #${BUILD_NUMBER} to ${params.ENV}?"
                        } else {
                            input "Perform rollback of build #${params.ROLLBACK_VERSION} to ${params.ENV}?"
                        }
                    }
                }
            }
        }

        stage('Deploy via Ansible') {
            steps {
                withAWS(credentials: 'aws-cred', region: params.REGION) {
                    withEnv(["AWS_REGION=${params.REGION}", "ANSIBLE_HOST_KEY_CHECKING=False"]) {
                        dir("${WORKSPACE}/ansible") {
                            sh """
                            ansible-playbook -i inventories/${params.ENV}/ec2.py playbooks/deploy.yml \
                            --extra-vars "artifact_version=${params.ROLLBACK ? params.ROLLBACK_VERSION : BUILD_NUMBER} env=${params.ENV} aws_region=${params.REGION}"
                            """
                        }
                    }
                }
            }
        }
    }
}

// // params text(name: 'EC2_REGIONS', defaultValue: 'us-east-1,us-east-2', description: 'Comma-separated list of EC2 regions to deploy to')
 
// // ec2 stage 
// // def ec2Regions = params.EC2_REGIONS.split(',')  // Split the input into a list

// // for (region in ec2Regions) {
// //     stage("Deploy to EC2 in ${region}") {
// //         steps {
//             withAWS(credentials: 'aws-cred', region: params.REGION) {
// //             withEnv(["AWS_REGION=${region.trim()}", "ANSIBLE_HOST_KEY_CHECKING=False"]) {
// //                 dir("${WORKSPACE}/ansible") {
// //                     sh """
// //                     ansible-playbook -i inventories/${params.ENV}/ec2.py playbooks/deploy.yml \
// //                     --extra-vars "artifact_version=${params.ROLLBACK ? params.ROLLBACK_VERSION : BUILD_NUMBER} env=${params.ENV} aws_region=${region.trim()}"
// //                     """
// //                 }
// //             }
//             }
// //         }
// //     }
// // }
