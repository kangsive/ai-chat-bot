'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../components/AuthProvider';
import { FiCheckCircle, FiXCircle, FiLoader } from 'react-icons/fi';

export default function VerifyEmailPage() {
  const { verifyEmail } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setIsLoading(false);
      setError('No verification token provided');
      return;
    }
    
    const verifyUserEmail = async () => {
      try {
        await verifyEmail(token);
        setIsSuccess(true);
      } catch (error) {
        console.error('Email verification error:', error);
        setError('Invalid or expired verification token');
      } finally {
        setIsLoading(false);
      }
    };
    
    verifyUserEmail();
  }, [searchParams, verifyEmail]);
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full text-center">
          <div className="flex justify-center">
            <FiLoader className="h-12 w-12 text-primary-500 animate-spin" />
          </div>
          <h2 className="mt-6 text-center text-xl font-medium text-gray-900">
            Verifying your email...
          </h2>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full text-center">
        {isSuccess ? (
          <>
            <div className="flex justify-center">
              <FiCheckCircle className="h-16 w-16 text-green-500" />
            </div>
            <h2 className="mt-6 text-center text-2xl font-bold text-gray-900">
              Email Verified Successfully!
            </h2>
            <p className="mt-2 text-center text-gray-600">
              Your email has been verified. You can now access all features of the platform.
            </p>
            <div className="mt-8">
              <Link
                href="/auth/login"
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Go to Login
              </Link>
            </div>
          </>
        ) : (
          <>
            <div className="flex justify-center">
              <FiXCircle className="h-16 w-16 text-red-500" />
            </div>
            <h2 className="mt-6 text-center text-2xl font-bold text-gray-900">
              Verification Failed
            </h2>
            <p className="mt-2 text-center text-gray-600">
              {error || 'There was an error verifying your email. Please try again.'}
            </p>
            <div className="mt-8 space-y-4">
              <p className="text-sm text-gray-600">
                If your verification link has expired, you can request a new one from your account settings.
              </p>
              <div className="flex flex-col space-y-3 sm:flex-row sm:space-y-0 sm:space-x-3 justify-center">
                <Link
                  href="/auth/login"
                  className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Go to Login
                </Link>
                <Link
                  href="/"
                  className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Return Home
                </Link>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
} 