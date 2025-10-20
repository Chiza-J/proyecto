import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { LogOut, Ticket, Filter } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TechnicianDashboard() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [allTickets, setAllTickets] = useState([]);
  const [assignedTickets, setAssignedTickets] = useState([]);
  const [resolvedTickets, setResolvedTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [allRes, assignedRes, resolvedRes] = await Promise.all([
        axios.get(`${API}/tickets`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/tickets/my-assigned`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/tickets/my-resolved`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setAllTickets(allRes.data);
      setAssignedTickets(assignedRes.data);
      setResolvedTickets(resolvedRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
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

  const TicketCard = ({ ticket }) => (
    <Card
      className="bg-white/70 backdrop-blur border-0 shadow-lg hover:shadow-xl cursor-pointer"
      onClick={() => navigate(`/ticket/${ticket.id}`)}
      data-testid={`tech-ticket-card-${ticket.id}`}
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
              <span>Cliente: <span className="font-medium text-gray-700">{ticket.user_name}</span></span>
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
  );

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
              <p className="text-sm text-gray-600">Panel de Técnico</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-gray-900">{user.name}</p>
              <p className="text-xs text-gray-500">{user.email}</p>
            </div>
            <Button variant="outline" size="sm" onClick={logout} data-testid="tech-logout-button">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-gray-900">{allTickets.length}</div>
              <div className="text-sm text-gray-600">Total Tickets</div>
            </CardContent>
          </Card>
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-blue-600">{allTickets.filter(t => t.status === "abierto").length}</div>
              <div className="text-sm text-gray-600">Abiertos</div>
            </CardContent>
          </Card>
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-amber-600">{assignedTickets.length}</div>
              <div className="text-sm text-gray-600">Asignados</div>
            </CardContent>
          </Card>
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-green-600">{resolvedTickets.length}</div>
              <div className="text-sm text-gray-600">Resueltos</div>
            </CardContent>
          </Card>
          <Card className="bg-white/70 backdrop-blur border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-red-600">{allTickets.filter(t => t.priority === "alta").length}</div>
              <div className="text-sm text-gray-600">Alta Prioridad</div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex items-center justify-between mb-6">
            <TabsList data-testid="tech-tabs">
              <TabsTrigger value="all" data-testid="all-tickets-tab">
                <Filter className="w-4 h-4 mr-2" />
                Todos ({allTickets.length})
              </TabsTrigger>
              <TabsTrigger value="assigned" data-testid="assigned-tickets-tab">
                Asignados a mí ({assignedTickets.length})
              </TabsTrigger>
              <TabsTrigger value="resolved" data-testid="resolved-tickets-tab">
                Resueltos por mí ({resolvedTickets.length})
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="all" className="space-y-4" data-testid="all-tickets-content">
            {allTickets.length === 0 ? (
              <Card className="bg-white/70 backdrop-blur">
                <CardContent className="py-12 text-center">
                  <Ticket className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">No hay tickets disponibles.</p>
                </CardContent>
              </Card>
            ) : (
              allTickets
                .sort((a, b) => {
                  const priorityOrder = { alta: 0, media: 1, baja: 2 };
                  return priorityOrder[a.priority] - priorityOrder[b.priority];
                })
                .map(ticket => <TicketCard key={ticket.id} ticket={ticket} />)
            )}
          </TabsContent>

          <TabsContent value="assigned" className="space-y-4" data-testid="assigned-tickets-content">
            {assignedTickets.length === 0 ? (
              <Card className="bg-white/70 backdrop-blur">
                <CardContent className="py-12 text-center">
                  <Ticket className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">No tienes tickets asignados.</p>
                </CardContent>
              </Card>
            ) : (
              assignedTickets.map(ticket => <TicketCard key={ticket.id} ticket={ticket} />)
            )}
          </TabsContent>

          <TabsContent value="resolved" className="space-y-4" data-testid="resolved-tickets-content">
            {resolvedTickets.length === 0 ? (
              <Card className="bg-white/70 backdrop-blur">
                <CardContent className="py-12 text-center">
                  <Ticket className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">Aún no has resuelto ningún ticket.</p>
                </CardContent>
              </Card>
            ) : (
              resolvedTickets.map(ticket => <TicketCard key={ticket.id} ticket={ticket} />)
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}