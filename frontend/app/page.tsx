'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (token) {
      router.push('/dashboard');
    }
  }, [router]);

  return (
    <div className="flex flex-col min-h-screen">
      <header className="bg-white shadow-sm py-4">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-800">AI Chatbot</h1>
          </div>
          <div className="space-x-4">
            <Link 
              href="/auth/login"
              className="px-4 py-2 text-primary-600 hover:text-primary-800 font-medium"
            >
              Login
            </Link>
            <Link
              href="/auth/register"
              className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600"
            >
              Sign Up
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-grow">
        <div className="container mx-auto px-4 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="md:w-1/2 mb-8 md:mb-0 pr-0 md:pr-8">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Your personal AI assistant
              </h2>
              <p className="text-xl text-gray-600 mb-6">
                Chat with our advanced AI to get answers, generate content, solve problems, and more.
              </p>
              <Link
                href="/auth/register"
                className="px-6 py-3 bg-primary-500 text-white rounded-md hover:bg-primary-600 inline-block font-medium"
              >
                Get Started
              </Link>
            </div>
            <div className="md:w-1/2">
              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="flex items-start mb-4">
                    <div className="bg-primary-100 text-primary-800 p-3 rounded-lg max-w-[80%]">
                      <p>How can AI assist me with my daily tasks?</p>
                    </div>
                  </div>
                  <div className="flex items-start justify-end mb-4">
                    <div className="bg-primary-500 text-white p-3 rounded-lg max-w-[80%]">
                      <p>
                        I can help you schedule meetings, draft emails, find information,
                        brainstorm ideas, solve problems, and much more. What specific tasks
                        do you need assistance with today?
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 