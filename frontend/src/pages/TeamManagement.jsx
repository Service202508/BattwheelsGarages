import { useState, useEffect } from "react";
import { API, getAuthHeaders } from "@/App";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { 
  Users, 
  UserPlus, 
  Mail, 
  Phone,
  Shield,
  Clock,
  Check,
  X,
  Trash2,
  RefreshCw,
  Copy,
  ExternalLink,
  AlertCircle,
  Crown,
  Settings
} from "lucide-react";
import { toast } from "sonner";

export default function TeamManagement({ user }) {
  const [members, setMembers] = useState([]);
  const [invites, setInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    name: "",
    email: "",
    role: "technician"
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchTeamData();
  }, []);

  const fetchTeamData = async () => {
    setLoading(true);
    try {
      const [membersRes, invitesRes] = await Promise.all([
        fetch(`${API}/organizations/me/members`, { headers: getAuthHeaders() }),
        fetch(`${API}/organizations/me/invites`, { headers: getAuthHeaders() })
      ]);

      if (membersRes.ok) {
        const data = await membersRes.json();
        setMembers(data.members || []);
      }
      if (invitesRes.ok) {
        const data = await invitesRes.json();
        setInvites(data.invites || []);
      }
    } catch (error) {
      console.error("Failed to fetch team data:", error);
      toast.error("Failed to load team data");
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const response = await fetch(`${API}/organizations/me/invite`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify(inviteForm)
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(`Invitation sent to ${inviteForm.email}`);
        setInviteDialogOpen(false);
        setInviteForm({ name: "", email: "", role: "technician" });
        fetchTeamData();
        
        // Show invite link for development
        if (data.invite_link) {
          toast.info(
            <div className="space-y-2">
              <p>Invite link (dev mode):</p>
              <code className="text-xs bg-[rgba(255,255,255,0.05)] p-1 rounded block truncate">
                {window.location.origin}{data.invite_link}
              </code>
            </div>,
            { duration: 10000 }
          );
        }
      } else {
        toast.error(data.detail || "Failed to send invitation");
      }
    } catch (error) {
      toast.error("Failed to send invitation");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelInvite = async (inviteId) => {
    try {
      const response = await fetch(`${API}/organizations/me/invites/${inviteId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });

      if (response.ok) {
        toast.success("Invitation cancelled");
        fetchTeamData();
      } else {
        const data = await response.json();
        toast.error(data.detail || "Failed to cancel invitation");
      }
    } catch (error) {
      toast.error("Failed to cancel invitation");
    }
  };

  const handleRemoveMember = async (userId) => {
    if (!confirm("Are you sure you want to remove this team member?")) return;
    
    try {
      const response = await fetch(`${API}/organizations/me/members/${userId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });

      if (response.ok) {
        toast.success("Team member removed");
        fetchTeamData();
      } else {
        const data = await response.json();
        toast.error(data.detail || "Failed to remove member");
      }
    } catch (error) {
      toast.error("Failed to remove member");
    }
  };

  const handleUpdateRole = async (userId, newRole) => {
    try {
      const response = await fetch(`${API}/organizations/me/members/${userId}/role`, {
        method: "PATCH",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ role: newRole })
      });

      if (response.ok) {
        toast.success("Role updated");
        fetchTeamData();
      } else {
        const data = await response.json();
        toast.error(data.detail || "Failed to update role");
      }
    } catch (error) {
      toast.error("Failed to update role");
    }
  };

  const copyInviteLink = (token) => {
    navigator.clipboard.writeText(`${window.location.origin}/accept-invite?token=${token}`);
    toast.success("Invite link copied to clipboard");
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      owner: "bg-amber-100 text-amber-700",
      admin: "bg-purple-100 text-[#8B5CF6]",
      manager: "bg-blue-100 text-[#3B9EFF]",
      technician: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
      accountant: "bg-teal-100 text-teal-700",
      viewer: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]"
    };
    return colors[role] || "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]";
  };

  const getStatusBadgeColor = (status) => {
    const colors = {
      pending: "bg-yellow-100 text-[#EAB308]",
      accepted: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
      expired: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]",
      cancelled: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]"
    };
    return colors[status] || "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]";
  };

  const getInitials = (name) => {
    if (!name) return "?";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const pendingInvites = invites.filter(i => i.status === "pending");

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-[rgba(244,246,240,0.45)]" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="team-management">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#F4F6F0]">Team Management</h1>
          <p className="text-[rgba(244,246,240,0.45)] mt-1">Manage your organization's team members and invitations</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchTeamData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
            <DialogTrigger asChild>
              <Button data-testid="invite-user-btn">
                <UserPlus className="h-4 w-4 mr-2" />
                Invite User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite Team Member</DialogTitle>
                <DialogDescription>
                  Send an invitation to join your organization
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleInvite} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    placeholder="John Doe"
                    value={inviteForm.name}
                    onChange={(e) => setInviteForm({ ...inviteForm, name: e.target.value })}
                    required
                    data-testid="invite-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="john@example.com"
                    value={inviteForm.email}
                    onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                    required
                    data-testid="invite-email-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Select
                    value={inviteForm.role}
                    onValueChange={(value) => setInviteForm({ ...inviteForm, role: value })}
                  >
                    <SelectTrigger data-testid="invite-role-select">
                      <SelectValue placeholder="Select a role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="manager">Manager</SelectItem>
                      <SelectItem value="technician">Technician</SelectItem>
                      <SelectItem value="accountant">Accountant</SelectItem>
                      <SelectItem value="viewer">Viewer</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">
                    {inviteForm.role === "admin" && "Full access to all features and settings"}
                    {inviteForm.role === "manager" && "Manage operations, no billing access"}
                    {inviteForm.role === "technician" && "Access to assigned tickets and tasks"}
                    {inviteForm.role === "accountant" && "Access to financial features only"}
                    {inviteForm.role === "viewer" && "Read-only access to data"}
                  </p>
                </div>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button type="button" variant="outline">Cancel</Button>
                  </DialogClose>
                  <Button type="submit" disabled={submitting} data-testid="send-invite-btn">
                    {submitting ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Mail className="h-4 w-4 mr-2" />
                        Send Invitation
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Users className="h-6 w-6 text-[#3B9EFF]" />
              </div>
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Team Members</p>
                <p className="text-2xl font-bold">{members.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Clock className="h-6 w-6 text-[#EAB308]" />
              </div>
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Pending Invites</p>
                <p className="text-2xl font-bold">{pendingInvites.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-[rgba(34,197,94,0.10)] rounded-lg">
                <Shield className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.45)]">Admins</p>
                <p className="text-2xl font-bold">
                  {members.filter(m => m.role === "admin" || m.role === "owner").length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="members" className="space-y-4">
        <TabsList>
          <TabsTrigger value="members" data-testid="members-tab">
            Team Members ({members.length})
          </TabsTrigger>
          <TabsTrigger value="invites" data-testid="invites-tab">
            Invitations ({invites.length})
          </TabsTrigger>
        </TabsList>

        {/* Members Tab */}
        <TabsContent value="members">
          <Card>
            <CardHeader>
              <CardTitle>Team Members</CardTitle>
              <CardDescription>
                People who have access to your organization
              </CardDescription>
            </CardHeader>
            <CardContent>
              {members.length === 0 ? (
                <div className="text-center py-8 text-[rgba(244,246,240,0.45)]">
                  <Users className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
                  <p>No team members yet</p>
                  <p className="text-sm">Invite your first team member to get started</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Member</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Joined</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {members.map((member) => (
                      <TableRow key={member.user_id} data-testid={`member-${member.user_id}`}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar className="h-9 w-9">
                              <AvatarFallback className="bg-indigo-100 text-indigo-700">
                                {getInitials(member.name)}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <div className="font-medium flex items-center gap-2">
                                {member.name}
                                {member.role === "owner" && (
                                  <Crown className="h-4 w-4 text-amber-500" />
                                )}
                                {member.user_id === user?.user_id && (
                                  <Badge variant="outline" className="text-xs">You</Badge>
                                )}
                              </div>
                              <p className="text-sm text-[rgba(244,246,240,0.45)]">{member.email}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {member.role === "owner" || member.user_id === user?.user_id ? (
                            <Badge className={getRoleBadgeColor(member.role)}>
                              {member.role}
                            </Badge>
                          ) : (
                            <Select
                              value={member.role}
                              onValueChange={(value) => handleUpdateRole(member.user_id, value)}
                            >
                              <SelectTrigger className="w-32 h-8">
                                <Badge className={getRoleBadgeColor(member.role)}>
                                  {member.role}
                                </Badge>
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="admin">Admin</SelectItem>
                                <SelectItem value="manager">Manager</SelectItem>
                                <SelectItem value="technician">Technician</SelectItem>
                                <SelectItem value="accountant">Accountant</SelectItem>
                                <SelectItem value="viewer">Viewer</SelectItem>
                              </SelectContent>
                            </Select>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-[rgba(244,246,240,0.45)]">
                          {member.joined_at 
                            ? new Date(member.joined_at).toLocaleDateString()
                            : "N/A"
                          }
                        </TableCell>
                        <TableCell>
                          <Badge className="bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]">Active</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {member.role !== "owner" && member.user_id !== user?.user_id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700 hover:bg-[rgba(255,59,47,0.08)]"
                              onClick={() => handleRemoveMember(member.user_id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invitations Tab */}
        <TabsContent value="invites">
          <Card>
            <CardHeader>
              <CardTitle>Invitations</CardTitle>
              <CardDescription>
                Pending and past invitations to your organization
              </CardDescription>
            </CardHeader>
            <CardContent>
              {invites.length === 0 ? (
                <div className="text-center py-8 text-[rgba(244,246,240,0.45)]">
                  <Mail className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
                  <p>No invitations sent yet</p>
                  <p className="text-sm">Invite team members using the button above</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invitee</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Sent</TableHead>
                      <TableHead>Expires</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invites.map((invite) => {
                      const isExpired = new Date(invite.expires_at) < new Date();
                      const status = isExpired && invite.status === "pending" ? "expired" : invite.status;
                      
                      return (
                        <TableRow key={invite.invite_id} data-testid={`invite-${invite.invite_id}`}>
                          <TableCell>
                            <div>
                              <p className="font-medium">{invite.name}</p>
                              <p className="text-sm text-[rgba(244,246,240,0.45)]">{invite.email}</p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge className={getRoleBadgeColor(invite.role)}>
                              {invite.role}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={getStatusBadgeColor(status)}>
                              {status === "pending" && <Clock className="h-3 w-3 mr-1" />}
                              {status === "accepted" && <Check className="h-3 w-3 mr-1" />}
                              {status === "expired" && <AlertCircle className="h-3 w-3 mr-1" />}
                              {status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm text-[rgba(244,246,240,0.45)]">
                            {new Date(invite.invited_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell className="text-sm text-[rgba(244,246,240,0.45)]">
                            {new Date(invite.expires_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell className="text-right">
                            {status === "pending" && (
                              <div className="flex justify-end gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => copyInviteLink(invite.token)}
                                  title="Copy invite link"
                                >
                                  <Copy className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-600 hover:text-red-700 hover:bg-[rgba(255,59,47,0.08)]"
                                  onClick={() => handleCancelInvite(invite.invite_id)}
                                  title="Cancel invitation"
                                >
                                  <X className="h-4 w-4" />
                                </Button>
                              </div>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
