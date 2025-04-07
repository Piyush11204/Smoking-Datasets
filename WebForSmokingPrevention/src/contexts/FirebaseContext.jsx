// src/contexts/FirebaseContext.js
import { createContext, useContext, useEffect, useState } from 'react';
import { 
  getAuth, 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword,
  onAuthStateChanged,
  signOut,
  updateProfile
} from 'firebase/auth';
import { getDatabase, ref, set, get, push, remove, update, onValue, off } from 'firebase/database';
import { initializeApp } from 'firebase/app';

// Your Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyCrMdlC0rNb7ko6lkfebWjKIAtGbmdiiNU",
  authDomain: "snoke-prevention.firebaseapp.com",
  databaseURL: "https://snoke-prevention-default-rtdb.firebaseio.com",
  projectId: "snoke-prevention",
  storageBucket: "snoke-prevention.appspot.com",
  messagingSenderId: "485983551438",
  appId: "1:485983551438:web:1ac2d215364b39d938359f",
  measurementId: "G-E11RB65093"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

// Create the context
const FirebaseContext = createContext(null);

// Create a custom hook to use the Firebase context
export const useFirebase = () => {
  return useContext(FirebaseContext);
};

// Create the Firebase provider component
export const FirebaseProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Auth functions
  const signup = async (email, password, userData) => {
    // Create user with email and password
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    
    // Update user profile with username
    await updateProfile(auth.currentUser, {
      username: userData.username,
      photoURL: userData.imageUrl || null
    });
    
    // Create user in database
    const user = {
      id: userCredential.user.uid,
      username: userData.username,
      imageUrl: userData.imageUrl || null,
      email: email,
      phoneNumber: userData.phoneNumber || "",
      password: password, // ⚠️ Avoid storing plaintext passwords in production
      createdAt: new Date().toISOString()
    };
    
    await setData(`users/${userCredential.user.uid}`, user);
    
    return userCredential;
  };

  const login = (email, password) => {
    return signInWithEmailAndPassword(auth, email, password);
  };

  const logout = () => {
    return signOut(auth);
  };

  // User management functions
  const getUserData = async (userId) => {
    return await getData(`users/${userId}`);
  };

  const updateUserData = async (userId, updates) => {
    return await updateData(`users/${userId}`, updates);
  };

  // Database functions
  const setData = async (path, data) => {
    const dbRef = ref(database, path);
    return await set(dbRef, data);
  };
  
  const getData = async (path) => {
    const dbRef = ref(database, path);
    const snapshot = await get(dbRef);
    return snapshot.exists() ? snapshot.val() : null;
  };
  
  const pushData = async (path, data) => {
    const dbRef = ref(database, path);
    const newRef = push(dbRef);
    await set(newRef, data);
    return newRef.key;
  };
  
  const updateData = async (path, updates) => {
    const dbRef = ref(database, path);
    return await update(dbRef, updates);
  };
  
  const removeData = async (path) => {
    const dbRef = ref(database, path);
    return await remove(dbRef);
  };
  
  const subscribeToData = (path, callback) => {
    const dbRef = ref(database, path);
    onValue(dbRef, (snapshot) => {
      const data = snapshot.val();
      callback(data);
    });
    
    // Return function to unsubscribe
    return () => off(dbRef);
  };

  // Set up auth state observer
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        // Get additional user data from database
        const userData = await getUserData(user.uid);
        
        if (userData) {
          // Use the user data structure that matches your Kotlin model
          setCurrentUser({
            id: user.uid,
            username: userData.username || user.username || "",
            imageUrl: userData.imageUrl || user.photoURL || null,
            email: userData.email || user.email || "",
            phoneNumber: userData.phoneNumber || "",
            password: userData.password || "" // Note: storing passwords like this is not recommended
          });
        } else {
          // Fallback if no user data in database
          setCurrentUser({
            id: user.uid,
            username: user.username || "",
            imageUrl: user.photoURL || null,
            email: user.email || "",
            phoneNumber: "",
            password: ""
          });
        }
      } else {
        setCurrentUser(null);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // Define the value to be provided to consumers
  const value = {
    currentUser,
    signup,
    login,
    logout,
    getUserData,
    updateUserData,
    setData,
    getData,
    pushData,
    updateData,
    removeData,
    subscribeToData
  };

  return (
    <FirebaseContext.Provider value={value}>
      {!loading && children}
    </FirebaseContext.Provider>
  );
};