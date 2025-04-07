import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Home as HomeIcon, LogIn, UserPlus, LogOut } from 'lucide-react';
import { useFirebase } from '../contexts/FirebaseContext';

function Navbar() {
  const { currentUser,getUserData, logout } = useFirebase(); // Assuming your FirebaseContext provides user and logout
  const navigate = useNavigate();
    console.log('User:', currentUser); // Debugging line to check user state
    console.log('User:', getUserData.userid); // Debugging line to check user state
  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold">
          <HomeIcon size={24} />
          MyApp
        </Link>
        <div className="flex items-center gap-6">
          {currentUser ? (
            <>
              <span className="flex items-center gap-2">
                Welcome, {currentUser.username || currentUser.displayName || currentUser.email} {/* Display username or email */}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 hover:text-blue-300"
              >
                <LogOut size={20} />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="flex items-center gap-2 hover:text-blue-300">
                <LogIn size={20} />
                Login
              </Link>
              <Link to="/register" className="flex items-center gap-2 hover:text-blue-300">
                <UserPlus size={20} />
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;