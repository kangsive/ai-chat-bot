import React from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import LoginForm from '../components/Auth/LoginForm';

const LoginPage: React.FC = () => {
  const router = useRouter();
  
  return (
    <Layout title="AI Chatbot - Login">
      <div className="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome Back
            </h1>
            <p className="mt-2 text-sm text-gray-600">
              Log in to continue chatting with AI
            </p>
          </div>
          
          <LoginForm />
          
          <div className="mt-4 text-center">
            <button
              onClick={() => router.push('/')}
              className="text-sm text-primary-600 hover:text-primary-800"
            >
              Return to Home
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default LoginPage; 