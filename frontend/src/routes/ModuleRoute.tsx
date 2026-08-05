import { Navigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { useDeployment } from "../context/useDeployment";
import { isModuleEnabled, type ModuleKey } from "../lib/moduleAccess";
import type { UserRole } from "../types/User";

type Props = {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
  requireModule?: ModuleKey;
  redirectTo?: string;
};

const ModuleRoute = ({
  children,
  allowedRoles,
  requireModule,
  redirectTo = "/dashboard",
}: Props) => {
  const { user, loading: authLoading } = useAuth();
  const { deployment, loading: deploymentLoading } = useDeployment();

  if (authLoading || (user !== null && deploymentLoading)) {
    return null;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={redirectTo} replace />;
  }
  if (requireModule && !isModuleEnabled(deployment, requireModule)) {
    return <Navigate to={redirectTo} replace />;
  }
  return <>{children}</>;
};

export default ModuleRoute;
