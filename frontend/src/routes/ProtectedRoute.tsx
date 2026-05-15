import { Navigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

type Props = {
  children: React.ReactNode;
  allowedRoles: ("admin" | "user" | "guest")[];
};

const ProtectedRoute = ({ children, allowedRoles }: Props) => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" />;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" />;
  }
  return <>{children}</>;
};

export default ProtectedRoute;
