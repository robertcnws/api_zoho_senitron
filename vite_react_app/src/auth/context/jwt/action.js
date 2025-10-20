import axios, { endpoints, axiosInstanceBackend } from 'src/utils/axios';

import { setSession } from './utils';
import { STORAGE_KEY } from './constant';

/** **************************************
 * Sign in
 *************************************** */
export const signInWithPassword = async ({ email, password }) => {
  try {
    const params = { email, password };

    const res = await axios.post(endpoints.auth.signIn, params);


    const { accessToken } = res.data;

    if (!accessToken) {
      throw new Error('Access token not found in response');
    }

    setSession(accessToken);
  } catch (error) {
    console.error('Error during sign in:', error);
    throw error;
  }
};

export const signInWithUsernameAndPassword = async ({ username, password, rememberMe }) => {
  try {
    const params = { username, password, rememberMe };

    const res = await axiosInstanceBackend.post(endpoints.auth.token, params, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    if (res.status === 200) {
      const { access, refresh } = res.data;
      if (!access || !refresh) throw new Error('Tokens not found');

      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);
      setSession(access);

      const loginResponse = await axiosInstanceBackend.post(endpoints.auth.login, params, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${access}`,
        },
      });

      if (loginResponse.status === 200) {
        delete loginResponse.data.data.password;
        console.log('Login Response Data:', loginResponse.data);
        localStorage.setItem('userLogged', JSON.stringify(loginResponse.data));
      }
      // setSession(accessToken);
    }

  } catch (error) {
    console.error('Error during sign in:', error);
    throw error;
  }
};

/** **************************************
 * Sign up
 *************************************** */
export const signUp = async ({ email, password, firstName, lastName }) => {
  const params = {
    email,
    password,
    firstName,
    lastName,
  };

  try {
    const res = await axiosInstanceBackend.post(endpoints.auth.signUp, params);

    const { accessToken } = res.data;

    if (!accessToken) {
      throw new Error('Access token not found in response');
    }

    sessionStorage.setItem(STORAGE_KEY, accessToken);
  } catch (error) {
    console.error('Error during sign up:', error);
    throw error;
  }
};

/** **************************************
 * Sign out
 *************************************** */
export const signOut = async () => {
  try {
    await setSession(null);
  } catch (error) {
    console.error('Error during sign out:', error);
    throw error;
  }
};
