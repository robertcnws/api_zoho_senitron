import axios, { axiosInstanceBackend, endpoints } from 'src/utils/axios';

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

export const signInWithUsernameAndPassword = async ({ username, password }) => {
  try {
    const params = { username, password };

    const res = await axiosInstanceBackend.post(endpoints.auth.token, params, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    if (res.status === 200) {
      localStorage.setItem('accessToken', res.data.access);
      localStorage.setItem('refreshToken', res.data.refresh);

      const accessToken = res.data.access;

      if (!accessToken) {
        throw new Error('Access token not found in response');
      }

      const loginResponse = await axiosInstanceBackend.post(endpoints.auth.login, params, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (loginResponse.status === 200) {
        delete loginResponse.data.data.password;
        localStorage.setItem('userLogged', JSON.stringify(loginResponse.data));
      }
      setSession(accessToken);
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
