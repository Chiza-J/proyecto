import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { ArrowLeft, Clock, User, Tag, FileText, MessageSquare, Image as ImageIcon, Edit } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TicketDetail() {
  const { ticketId } = useParams();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [technicians, setTechnicians] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [editMode, setEditMode] = useState({
    status: false,
    priority: false,
    technician: false
  });

  useEffect(() => {
    fetchTicket();
    if (user.role !== "cliente") {
      fetchTechnicians();
    }
  }, [ticketId]);

  const fetchTicket = async () => {
    try {
      const response = await axios.get(`${API}/tickets/${ticketId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTicket(response.data);
    } catch (error) {
      toast.error("Error al cargar ticket");
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const fetchTechnicians = async () => {
    try {
      const response = await axios.get(`${API}/users/technicians`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTechnicians(response.data);
    } catch (error) {
      console.error("Error loading technicians:", error);
    }
  };

  const handleUpdateTicket = async (field, value) => {
    setUpdating(true);
    try {
      const updateData = { [field]: value };
      await axios.put(`${API}/tickets/${ticketId}`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Ticket actualizado");
      fetchTicket();
      setEditMode({ ...editMode, [field]: false });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar ticket");
    } finally {
      setUpdating(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      await axios.post(
        `${API}/tickets/${ticketId}/comments`,
        { comment: newComment },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Comentario agregado");
      setNewComment("");
      fetchTicket();
    } catch (error) {
      toast.error("Error al agregar comentario");
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "baja": return "bg-green-500";
      case "media": return "bg-yellow-500";
      case "alta": return "bg-red-500";
      default: return "bg-gray-500";
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      "abierto": "bg-blue-100 text-blue-800",
      "en_proceso": "bg-amber-100 text-amber-800",
      "cerrado": "bg-green-100 text-green-800"
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  const getTimeElapsed = (date) => {
    const now = new Date();
    const created = new Date(date);
    const diffMs = now - created;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays} día${diffDays > 1 ? 's' : ''}`;
    }
    return `${diffHours} hora${diffHours !== 1 ? 's' : ''}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Cargando...</div>
      </div>
    );
  }

  if (!ticket) return null;

  const isTechnician = user.role === "tecnico" || user.role === "admin";

  return (
    <div className="min-h-screen" style={{
      background: 'linear-gradient(to bottom, #e0f7f4 0%, #ffffff 100%)'
    }}>
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Button
            variant="ghost"
            onClick={() => navigate("/dashboard")}
            data-testid="back-to-dashboard-button"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver al Dashboard
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Ticket Info */}
            <Card className="bg-white/70 backdrop-blur border-0 shadow-lg" data-testid="ticket-detail-card">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`w-4 h-4 rounded-full ${getPriorityColor(ticket.priority)} mt-1`}></div>
                    <div>
                      <CardTitle className="text-2xl mb-2">{ticket.title}</CardTitle>
                      <div className="flex gap-2">
                        <Badge className={getStatusBadge(ticket.status)}>
                          {ticket.status.replace('_', ' ')}
                        </Badge>
                        <Badge variant="outline" className="capitalize">{ticket.priority}</Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Descripción</h3>
                  <p className="text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
                </div>

                {/* Attachments */}
                {ticket.attachments && ticket.attachments.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                      <ImageIcon className="w-4 h-4" />
                      Archivos Adjuntos ({ticket.attachments.length})
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {ticket.attachments.map(att => (
                        <div key={att.id} className="relative group">
                          <img
                            src={`data:image/jpeg;base64,${att.file_data}`}
                            alt={att.filename}
                            className="w-full h-40 object-cover rounded-lg border border-gray-200"
                          />
                          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                            <span className="text-white text-xs text-center px-2">{att.filename}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Separator />

                {/* Comments Section */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    Comentarios ({ticket.comments?.length || 0})
                  </h3>

                  <ScrollArea className="h-80 pr-4">
                    <div className="space-y-4">
                      {ticket.comments && ticket.comments.length > 0 ? (
                        ticket.comments.map(comment => (
                          <div key={comment.id} className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-start justify-between mb-2">
                              <span className="font-medium text-gray-900">{comment.user_name}</span>
                              <span className="text-xs text-gray-500">
                                {new Date(comment.created_at).toLocaleString('es-ES')}
                              </span>
                            </div>
                            <p className="text-gray-700">{comment.comment}</p>
                          </div>
                        ))
                      ) : (
                        <p className="text-gray-500 text-center py-8">No hay comentarios aún</p>
                      )}
                    </div>
                  </ScrollArea>

                  {/* Add Comment */}
                  <form onSubmit={handleAddComment} className="mt-4">
                    <Textarea
                      placeholder="Escribe un comentario..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      rows={3}
                      className="mb-2"
                      data-testid="comment-input"
                    />
                    <Button type="submit" className="bg-teal-600 hover:bg-teal-700" data-testid="submit-comment-button">
                      Agregar Comentario
                    </Button>
                  </form>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Details Card */}
            <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg">Detalles del Ticket</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                    <User className="w-4 h-4" />
                    Cliente
                  </div>
                  <p className="font-medium text-gray-900">{ticket.user?.name}</p>
                </div>

                <Separator />

                <div>
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                    <Tag className="w-4 h-4" />
                    Categoría
                  </div>
                  <p className="font-medium text-gray-900">{ticket.category?.name}</p>
                </div>

                {ticket.equipment && (
                  <>
                    <Separator />
                    <div>
                      <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                        <FileText className="w-4 h-4" />
                        Equipo
                      </div>
                      <p className="font-medium text-gray-900">{ticket.equipment.name}</p>
                      <p className="text-sm text-gray-600">{ticket.equipment.type}</p>
                    </div>
                  </>
                )}

                <Separator />

                <div>
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                    <Clock className="w-4 h-4" />
                    Tiempo Transcurrido
                  </div>
                  <p className="font-medium text-gray-900">{getTimeElapsed(ticket.created_at)}</p>
                  <p className="text-xs text-gray-500">
                    Creado: {new Date(ticket.created_at).toLocaleString('es-ES')}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Actions Card (Only for technicians) */}
            {isTechnician && (
              <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Edit className="w-4 h-4" />
                    Acciones de Técnico
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Status */}
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">Estado</label>
                    <Select
                      value={ticket.status}
                      onValueChange={(value) => handleUpdateTicket("status", value)}
                      disabled={updating}
                    >
                      <SelectTrigger data-testid="status-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="abierto">Abierto</SelectItem>
                        <SelectItem value="en_proceso">En Proceso</SelectItem>
                        <SelectItem value="cerrado">Cerrado</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Priority */}
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">Prioridad</label>
                    <Select
                      value={ticket.priority}
                      onValueChange={(value) => handleUpdateTicket("priority", value)}
                      disabled={updating}
                    >
                      <SelectTrigger data-testid="priority-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="baja">Baja</SelectItem>
                        <SelectItem value="media">Media</SelectItem>
                        <SelectItem value="alta">Alta</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Assign Technician */}
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">Asignar Técnico</label>
                    <Select
                      value={ticket.technician_id || ""}
                      onValueChange={(value) => handleUpdateTicket("technician_id", value)}
                      disabled={updating}
                    >
                      <SelectTrigger data-testid="technician-select">
                        <SelectValue placeholder="Seleccionar técnico" />
                      </SelectTrigger>
                      <SelectContent>
                        {technicians.map(tech => (
                          <SelectItem key={tech.id} value={tech.id}>{tech.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* History Card */}
            <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg">Historial</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-60">
                  <div className="space-y-3">
                    {ticket.history && ticket.history.length > 0 ? (
                      ticket.history.map((hist, index) => (
                        <div key={hist.id} className="relative pl-4 pb-3 border-l-2 border-gray-200 last:border-0">
                          <div className="absolute left-0 top-0 w-2 h-2 -translate-x-[5px] rounded-full bg-teal-500"></div>
                          <p className="text-sm text-gray-900">{hist.action}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {hist.user_name} - {new Date(hist.timestamp).toLocaleString('es-ES')}
                          </p>
                        </div>
                      ))
                    ) : (
                      <p className="text-gray-500 text-sm text-center py-4">Sin historial</p>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
