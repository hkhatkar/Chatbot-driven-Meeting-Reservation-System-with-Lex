# Agentic Meeting Reservations Chatbot Project

Welcome to the **Agentic Meeting Reservations Chatbot Project**! This repository aims to leverage AWS Lex (A service behind Amazon's Alexa) to build a flexible meeting reservation system with a chatbot interface, based on different businesses Room and Employee configuration and data.

## Project Demo

A demo of the web application front-end built with react + vite, using API gateway to integrate DynamoDB data and the Lex service:
https://youtu.be/fuTUrf6l2GA

---

## Credits

Built using LexV2 Documentation: https://docs.aws.amazon.com/lexv2/latest/dg/what-is.html

---

## Project Overview
Application: This project is designed to simplify and streamline the process of booking meeting rooms and managing employee schedules through an intelligent chatbot interface. Traditional booking systems often require navigating complex calendars or multiple platforms, leading to inefficient user experiences and booking conflicts.
Our task is to build a web application that displays bookings information, which can be altered by a customized conversational interface.

In this project:
1. Use Amazon CDK to build an end to end AWS Stack, and to easily deploy across AWS accounts 
2. Build a custom chatbot using AWS Lex for the purpose of meeting reservations
3. Design and set up a DynamoDB database system for Bookings, Employees and Rooms data
4. Use AWS Lambda to manage agentic tasks based on user utterances via chatbot 
5. Developed a sample front-end using react, vite and tailwindcss
6. Use AWS Amplify to handle frontend integration and authentication of AWS services
7. Use API Gateway to expose REST API endpoints backed by our Lambda function to enable our frontend web app to securely interact with backend booking data
8. Host the website using S3 and Cloudfront

---

## File overview

### **cdk**
 - 1-aws_lex_chatbot_stack.py - main stack configuration, defines the cdk stack to deploy
 - 2-lex_bot.py - defines the lex chatbot configuration, substack of aws_lex_chatbot_stack.py
### **frontend**
 - 1-main.jsx - main web app javascript, XML file, uses AWS Amplify to handle chatbot integration
 - 2-App.jsx - covers interface, including bookings data display and handling of chatbot input/outputs
 - 3-ConfigContext.jsx - updated by main.jsx to store configuration information of Amplify. Used in App.jsx to send/ recieve requests from Lex service
### **lambdas**
 - 1-init_db.py - writes sample data to the dynamodb tables for staff, bookings and rooms
 - 2-sample_data.json - sample data for dynamodb tables used by init_db.py
 - 3-unified_lambda.py - lambda function that handles tasks based on Lex utterances including booking meetings, checking availability and validation


---

## Technologies Used

This project makes use of the following technologies:

- **Languages** - Python, Javascript, XML, CSS
- **Cloud** - Amazon Lex, AWS CDK, DynamoDB, Lambda, AWS Amplify, API Gateway, S3, Cloudfront, IAM
- **React** - Tailwindcss, vite

---

## Setup
### **CDK Setup**
- 1.1 Download AWS CLI v2:
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install

- 1.2 configure AWS CLI with your credentials using: 
        aws configure
    
- 1.3 Make sure Node.js and npm are installed, and install AWS CDK CLI globally:
        npm install -g aws-cdk

- 1.4 Clone this repository and install dependancies with npm install

- 1.5 Bootstrap your AWS environment using:
        cdk bootstrap aws://ACCOUNT-NUMBER/REGION


### **Project Deployement**
- 2.1 In project root activate the python venv with:
        source .venv/bin/activate

- 2.2 cd into the frontend/react-app folder and build your the react app with:
        npm run build

- 2.3 To deploy the services to AWS, in the project root run:
        cdk deploy

- 2.4 Head to AWS Console > Cloud formation > AwsLexChatbotStack > Outputs : You will find a WebsiteURL to test the application

