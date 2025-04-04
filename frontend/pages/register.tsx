import React from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import RegisterForm from '../components/Auth/RegisterForm';

const RegisterPage: React.FC = () => {
  const router = useRouter();
  
  return (
    <Layout title="AI Chatbot - Register">
      <div className="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold text-gray-900">
              Create Your Account
            </h1>
            <p className="mt-2 text-sm text-gray-600">
              Sign up to start chatting with our AI
            </p>
          </div>
          
          <RegisterForm />
          
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

export default RegisterPage; 