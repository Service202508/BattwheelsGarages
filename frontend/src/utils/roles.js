export function getUserRole(user) {
  return (user?.role || "").toLowerCase();
}

export function canAccessEVFI(user) {
  const role = getUserRole(user);
  return ["owner", "admin", "org_admin", "manager", "technician"].includes(role);
}

export function canManageTicket(user) {
  const role = getUserRole(user);
  return ["owner", "admin", "org_admin", "manager", "technician", "dispatcher"].includes(role);
}

export function canAccessFinance(user) {
  const role = getUserRole(user);
  return ["owner", "admin", "org_admin", "accountant"].includes(role);
}

export function canManageTeam(user) {
  const role = getUserRole(user);
  return ["owner", "admin", "org_admin"].includes(role);
}

export function canEditEstimate(user) {
  const role = getUserRole(user);
  return ["owner", "admin", "org_admin", "manager", "technician"].includes(role);
}

export function isOwnerOrAdmin(user) {
  const role = getUserRole(user);
  return ["owner", "admin", "org_admin"].includes(role);
}
