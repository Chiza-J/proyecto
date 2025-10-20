import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, LogOut, Ticket, Upload, X } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ClientDashboard() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [equipments, setEquipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newTicket, setNewTicket] = useState({
    title: "",
    description: "",
    category_id: "",
    equipment_id: "",
    attachments: []
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ticketsRes, categoriesRes, equipmentsRes] = await Promise.all([
        axios.get(`${API}/tickets`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/categories`),
        axios.get(`${API}/equipments`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setTickets(ticketsRes.data);
      setCategories(categoriesRes.data);
      setEquipments(equipmentsRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result.split(',')[1];
        setNewTicket(prev => ({
          ...prev,
          attachments: [...prev.attachments, { filename: file.name, file_data: base64 }]
        }));
      };
      reader.readAsDataURL(file);
    });
  };

  const removeAttachment = (index) => {
    setNewTicket(prev => ({
      ...prev,
      attachments: prev.attachments.filter((_, i) => i !== index)
    }));
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/tickets`, newTicket, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Ticket creado exitosamente");
      setCreateDialogOpen(false);
      setNewTicket({ title: "", description: "", category_id: "", equipment_id: "", attachments: [] });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear ticket");
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{
      background: 'linear-gradient(to bottom, #e0f7f4 0%, #ffffff 100%)'
    }}>
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-lg flex items-center justify-center">
              <Ticket className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">TechAssist</h1>
              <p className="text-sm text-gray-600">Panel de Cliente</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-gray-900">{user.name}</p>
              <p className="text-xs text-gray-500">{user.email}</p>
            </div>
            <Button variant="outline" size="sm" onClick={logout} data-testid="logout-button">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-gray-900">{tickets.length}</div>
              <div className="text-sm text-gray-600">Total Tickets</div>
            </CardContent>
          </Card>
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-blue-600">{tickets.filter(t => t.status === "abierto").length}</div>
              <div className="text-sm text-gray-600">Abiertos</div>
            </CardContent>
          </Card>
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-amber-600">{tickets.filter(t => t.status === "en_proceso").length}</div>
              <div className="text-sm text-gray-600">En Proceso</div>
            </CardContent>
          </Card>
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-green-600">{tickets.filter(t => t.status === "cerrado").length}</div>
              <div className="text-sm text-gray-600">Cerrados</div>
            </CardContent>
          </Card>
        </div>

        {/* Create Ticket Button */}
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">Mis Tickets</h2>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-teal-600 hover:bg-teal-700" data-testid="create-ticket-button">
                <Plus className="w-4 h-4 mr-2" />
                Crear Ticket
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="create-ticket-dialog">
              <DialogHeader>
                <DialogTitle>Crear Nuevo Ticket</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateTicket} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Título</Label>
                  <Input
                    id="title"
                    data-testid="ticket-title-input"
                    value={newTicket.title}
                    onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
                    required
                    placeholder="Describe brevemente el problema"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Descripción</Label>
                  <Textarea
                    id="description"
                    data-testid="ticket-description-input"
                    value={newTicket.description}
                    onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                    required
                    rows={4}
                    placeholder="Describe detalladamente el problema..."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Categoría</Label>
                  <Select
                    value={newTicket.category_id}
                    onValueChange={(value) => setNewTicket({ ...newTicket, category_id: value })}
                    required
                  >
                    <SelectTrigger data-testid="ticket-category-select">
                      <SelectValue placeholder="Selecciona una categoría" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(cat => (
                        <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="equipment">Equipo (Opcional)</Label>
                  <Select
                    value={newTicket.equipment_id}
                    onValueChange={(value) => setNewTicket({ ...newTicket, equipment_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona un equipo" />
                    </SelectTrigger>
                    <SelectContent>
                      {equipments.map(eq => (
                        <SelectItem key={eq.id} value={eq.id}>{eq.name} - {eq.type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="attachments">Adjuntar Imágenes</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="attachments"
                      data-testid="ticket-attachment-input"
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={handleFileUpload}
                      className="cursor-pointer"
                    />
                    <Upload className="w-5 h-5 text-gray-400" />
                  </div>
                  {newTicket.attachments.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {newTicket.attachments.map((att, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                          <span className="text-sm text-gray-700">{att.filename}</span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeAttachment(index)}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700" data-testid="submit-ticket-button">
                  Crear Ticket
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Tickets List */}
        <div className="grid gap-4">
          {tickets.length === 0 ? (
            <Card className="bg-white/70 backdrop-blur">
              <CardContent className="py-12 text-center">
                <Ticket className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">No tienes tickets aún. Crea uno para comenzar.</p>
              </CardContent>
            </Card>
          ) : (
            tickets.map(ticket => (
              <Card
                key={ticket.id}
                className="bg-white/70 backdrop-blur border-0 shadow-lg hover:shadow-xl cursor-pointer"
                onClick={() => navigate(`/ticket/${ticket.id}`)}
                data-testid={`ticket-card-${ticket.id}`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className={`w-3 h-3 rounded-full ${getPriorityColor(ticket.priority)} mt-2`}></div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-1">{ticket.title}</h3>
                          <p className="text-sm text-gray-600 line-clamp-2">{ticket.description}</p>
                        </div>
                        <Badge className={getStatusBadge(ticket.status)}>
                          {ticket.status.replace('_', ' ')}
                        </Badge>
                      </div>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-500 mt-3">
                        <span>Categoría: <span className="font-medium text-gray-700">{ticket.category_name}</span></span>
                        <span>Prioridad: <span className="font-medium text-gray-700">{ticket.priority}</span></span>
                        {ticket.technician_name && (
                          <span>Técnico: <span className="font-medium text-gray-700">{ticket.technician_name}</span></span>
                        )}
                        <span className="ml-auto">{new Date(ticket.created_at).toLocaleDateString('es-ES')}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}