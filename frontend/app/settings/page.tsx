'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { FiUser, FiMail, FiLock, FiSave, FiLoader, FiArrowLeft } from 'react-icons/fi';
import { useAuth } from '../components/AuthProvider';
import { configApi } from '../lib/api';
import toast from 'react-hot-toast';

interface UserConfig {
  theme: string;
  language: string;
  model_preference: string;
  response_length: string;
  response_tone: string;
  notifications_enabled: boolean;
}

const defaultConfig: UserConfig = {
  theme: 'light',
  language: 'en',
  model_preference: 'default',
  response_length: 'medium',
  response_tone: 'balanced',
  notifications_enabled: true,
};

export default function SettingsPage() {
  const { user, updateProfile } = useAuth();
  const router = useRouter();
  
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    email: '',
    username: '',
  });
  
  const [config, setConfig] = useState<UserConfig>(defaultConfig);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  
  // Load user data into form
  useEffect(() => {
    if (user) {
      setProfileForm({
        full_name: user.full_name || '',
        email: user.email,
        username: user.username,
      });
    }
  }, [user]);
  
  // Load user config
  useEffect(() => {
    const fetchUserConfig = async () => {
      try {
        const response = await configApi.getUserConfig();
        if (response && response.preferences) {
          setConfig({
            ...defaultConfig,
            ...response.preferences,
          });
        }
      } catch (error) {
        console.error('Error fetching user config:', error);
        toast.error('Failed to load user preferences');
      }
    };
    
    if (user) {
      fetchUserConfig();
    }
  }, [user]);
  
  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfileForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };
  
  const handleConfigChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    
    setConfig((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };
  
  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsLoadingProfile(true);
      await updateProfile({
        full_name: profileForm.full_name || undefined,
      });
      toast.success('Profile updated successfully');
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      setIsLoadingProfile(false);
    }
  };
  
  const handleConfigSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsLoadingConfig(true);
      await configApi.updateUserConfig(config);
      toast.success('Preferences updated successfully');
    } catch (error) {
      console.error('Error updating config:', error);
      toast.error('Failed to update preferences');
    } finally {
      setIsLoadingConfig(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex items-center">
          <Link
            href="/dashboard"
            className="mr-4 flex items-center text-gray-600 hover:text-gray-900"
          >
            <FiArrowLeft className="h-5 w-5 mr-1" />
            Back to Dashboard
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Settings</h1>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex flex-col md:flex-row">
            {/* Tab navigation */}
            <div className="md:w-64 mb-8 md:mb-0">
              <nav className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Settings</h3>
                </div>
                <div className="border-t border-gray-200 px-0">
                  <ul className="divide-y divide-gray-200">
                    <li>
                      <button
                        onClick={() => setActiveTab('profile')}
                        className={`w-full px-4 py-4 flex items-center text-left ${
                          activeTab === 'profile' ? 'bg-gray-50 text-primary-700' : 'text-gray-700'
                        }`}
                      >
                        <FiUser className="mr-3 h-5 w-5" />
                        <span>Profile</span>
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => setActiveTab('preferences')}
                        className={`w-full px-4 py-4 flex items-center text-left ${
                          activeTab === 'preferences' ? 'bg-gray-50 text-primary-700' : 'text-gray-700'
                        }`}
                      >
                        <FiUser className="mr-3 h-5 w-5" />
                        <span>AI Preferences</span>
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => setActiveTab('security')}
                        className={`w-full px-4 py-4 flex items-center text-left ${
                          activeTab === 'security' ? 'bg-gray-50 text-primary-700' : 'text-gray-700'
                        }`}
                      >
                        <FiLock className="mr-3 h-5 w-5" />
                        <span>Security</span>
                      </button>
                    </li>
                  </ul>
                </div>
              </nav>
            </div>
            
            {/* Content area */}
            <div className="md:flex-1 md:ml-8">
              <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                {/* Profile settings */}
                {activeTab === 'profile' && (
                  <div>
                    <div className="px-4 py-5 sm:px-6">
                      <h3 className="text-lg leading-6 font-medium text-gray-900">Profile Settings</h3>
                      <p className="mt-1 max-w-2xl text-sm text-gray-500">
                        Manage your personal information
                      </p>
                    </div>
                    <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                      <form onSubmit={handleProfileSubmit}>
                        <div className="space-y-6">
                          <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                              Username
                            </label>
                            <div className="mt-1 relative rounded-md shadow-sm">
                              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <FiUser className="h-5 w-5 text-gray-400" />
                              </div>
                              <input
                                type="text"
                                name="username"
                                id="username"
                                value={profileForm.username}
                                readOnly
                                disabled
                                className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md bg-gray-50"
                              />
                            </div>
                            <p className="mt-1 text-xs text-gray-500">Username cannot be changed</p>
                          </div>
                          
                          <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                              Email
                            </label>
                            <div className="mt-1 relative rounded-md shadow-sm">
                              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <FiMail className="h-5 w-5 text-gray-400" />
                              </div>
                              <input
                                type="email"
                                name="email"
                                id="email"
                                value={profileForm.email}
                                readOnly
                                disabled
                                className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md bg-gray-50"
                              />
                            </div>
                            <p className="mt-1 text-xs text-gray-500">
                              Contact support to change your email address
                            </p>
                          </div>
                          
                          <div>
                            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                              Full Name
                            </label>
                            <div className="mt-1">
                              <input
                                type="text"
                                name="full_name"
                                id="full_name"
                                value={profileForm.full_name}
                                onChange={handleProfileChange}
                                className="focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              />
                            </div>
                          </div>
                          
                          <div className="flex justify-end">
                            <button
                              type="submit"
                              disabled={isLoadingProfile}
                              className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                                isLoadingProfile 
                                  ? 'bg-primary-400' 
                                  : 'bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
                              }`}
                            >
                              {isLoadingProfile ? (
                                <>
                                  <FiLoader className="animate-spin -ml-1 mr-2 h-4 w-4" />
                                  Saving...
                                </>
                              ) : (
                                <>
                                  <FiSave className="-ml-1 mr-2 h-4 w-4" />
                                  Save Changes
                                </>
                              )}
                            </button>
                          </div>
                        </div>
                      </form>
                    </div>
                  </div>
                )}
                
                {/* AI Preferences settings */}
                {activeTab === 'preferences' && (
                  <div>
                    <div className="px-4 py-5 sm:px-6">
                      <h3 className="text-lg leading-6 font-medium text-gray-900">AI Preferences</h3>
                      <p className="mt-1 max-w-2xl text-sm text-gray-500">
                        Customize your AI assistant experience
                      </p>
                    </div>
                    <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                      <form onSubmit={handleConfigSubmit}>
                        <div className="space-y-6">
                          <div>
                            <label htmlFor="theme" className="block text-sm font-medium text-gray-700">
                              Theme
                            </label>
                            <select
                              id="theme"
                              name="theme"
                              value={config.theme}
                              onChange={handleConfigChange}
                              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                            >
                              <option value="light">Light</option>
                              <option value="dark">Dark</option>
                              <option value="system">System</option>
                            </select>
                          </div>
                          
                          <div>
                            <label htmlFor="language" className="block text-sm font-medium text-gray-700">
                              Language
                            </label>
                            <select
                              id="language"
                              name="language"
                              value={config.language}
                              onChange={handleConfigChange}
                              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                            >
                              <option value="en">English</option>
                              <option value="fr">French</option>
                              <option value="es">Spanish</option>
                              <option value="de">German</option>
                              <option value="zh">Chinese</option>
                            </select>
                          </div>
                          
                          <div>
                            <label htmlFor="model_preference" className="block text-sm font-medium text-gray-700">
                              AI Model
                            </label>
                            <select
                              id="model_preference"
                              name="model_preference"
                              value={config.model_preference}
                              onChange={handleConfigChange}
                              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                            >
                              <option value="default">Default</option>
                              <option value="gpt-4">GPT-4 (Premium)</option>
                              <option value="gpt-3.5">GPT-3.5 Turbo</option>
                            </select>
                          </div>
                          
                          <div>
                            <label htmlFor="response_length" className="block text-sm font-medium text-gray-700">
                              Response Length
                            </label>
                            <select
                              id="response_length"
                              name="response_length"
                              value={config.response_length}
                              onChange={handleConfigChange}
                              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                            >
                              <option value="short">Short</option>
                              <option value="medium">Medium</option>
                              <option value="long">Long</option>
                            </select>
                          </div>
                          
                          <div>
                            <label htmlFor="response_tone" className="block text-sm font-medium text-gray-700">
                              Response Tone
                            </label>
                            <select
                              id="response_tone"
                              name="response_tone"
                              value={config.response_tone}
                              onChange={handleConfigChange}
                              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                            >
                              <option value="formal">Formal</option>
                              <option value="balanced">Balanced</option>
                              <option value="casual">Casual</option>
                              <option value="friendly">Friendly</option>
                            </select>
                          </div>
                          
                          <div className="flex items-start">
                            <div className="flex items-center h-5">
                              <input
                                id="notifications_enabled"
                                name="notifications_enabled"
                                type="checkbox"
                                checked={config.notifications_enabled}
                                onChange={handleConfigChange}
                                className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                              />
                            </div>
                            <div className="ml-3 text-sm">
                              <label htmlFor="notifications_enabled" className="font-medium text-gray-700">
                                Enable notifications
                              </label>
                              <p className="text-gray-500">Get notified about AI responses and important updates.</p>
                            </div>
                          </div>
                          
                          <div className="flex justify-end">
                            <button
                              type="submit"
                              disabled={isLoadingConfig}
                              className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                                isLoadingConfig 
                                  ? 'bg-primary-400' 
                                  : 'bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
                              }`}
                            >
                              {isLoadingConfig ? (
                                <>
                                  <FiLoader className="animate-spin -ml-1 mr-2 h-4 w-4" />
                                  Saving...
                                </>
                              ) : (
                                <>
                                  <FiSave className="-ml-1 mr-2 h-4 w-4" />
                                  Save Preferences
                                </>
                              )}
                            </button>
                          </div>
                        </div>
                      </form>
                    </div>
                  </div>
                )}
                
                {/* Security settings */}
                {activeTab === 'security' && (
                  <div>
                    <div className="px-4 py-5 sm:px-6">
                      <h3 className="text-lg leading-6 font-medium text-gray-900">Security Settings</h3>
                      <p className="mt-1 max-w-2xl text-sm text-gray-500">
                        Manage your account security
                      </p>
                    </div>
                    <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                      <div className="space-y-6">
                        <div>
                          <h4 className="text-base font-medium text-gray-900">Change Password</h4>
                          <p className="mt-1 text-sm text-gray-500">
                            You can reset your password by clicking the button below.
                          </p>
                          <div className="mt-3">
                            <Link
                              href="/auth/reset-password"
                              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                            >
                              <FiLock className="-ml-1 mr-2 h-4 w-4" />
                              Reset Password
                            </Link>
                          </div>
                        </div>
                        
                        <div className="border-t border-gray-200 pt-5">
                          <h4 className="text-base font-medium text-gray-900">Email Verification</h4>
                          <p className="mt-1 text-sm text-gray-500">
                            {user?.is_verified 
                              ? 'Your email has been verified.' 
                              : 'Please verify your email to access all features.'}
                          </p>
                          {!user?.is_verified && (
                            <div className="mt-3">
                              <button 
                                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                              >
                                <FiMail className="-ml-1 mr-2 h-4 w-4" />
                                Resend Verification Email
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 