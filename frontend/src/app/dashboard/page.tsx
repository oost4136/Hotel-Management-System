"use client";

import { motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  BedDouble,
  Hotel,
  LayoutDashboard,
  LogOut,
  Save,
  Search,
  Settings,
  Trash2,
  TrendingUp,
  UserPlus,
  Users,
  Package,
  CheckCircle2,
  LifeBuoy,
  Plus,
  Minus,
  ShoppingCart,
} from "lucide-react";
import { apiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

type User = { id: number; username: string; role: string };
type DashboardStats = { total_bookings: number; active_guests: number; available_rooms: number; total_rooms: number };
type AppSettings = { business_name: string; primary_color: string; caution_fee: number; logo_path: string; currency_symbol: string };
type Room = { id: number; name: string; price: number; caution_fee: number; is_available: number; image_url?: string; amenities?: string };
type Staff = { id: number; username: string; role: string };
type RecentBooking = { id: number; customer_name: string; room_name: string | null; status: string; caution_fee: number | null; room_price: number | null };
type ActivityLog = { id: number; username: string; action: string; details: string; timestamp: string };
type InventoryItem = { id: number; item_name: string; price: number; stock_level: number; category: string; image_path?: string };
type ActiveBooking = { booking_id: number; customer_name: string; guest_phone: string; check_in: string; check_out: string | null; caution_fee: number; room_id: number; room_name: string; room_price: number };
type Tab = "overview" | "rooms" | "checkin" | "active-guests" | "inventory" | "staff" | "settings" | "help";
type BookingCreate = { customer_name: string; guest_phone: string; room_id: number; adults: number; children: number; caution_fee: number };
type InventoryItemCreate = { item_name: string; price: number; stock_level: number; category: string; image_path?: string };
type SaleCreate = { booking_id: number | null; guest_name?: string; item_id: number; item_name: string; quantity: number; price: number; payment_status: string };

const emptySettings: AppSettings = {
  business_name: "",
  primary_color: "#2ecc71",
  caution_fee: 0,
  logo_path: "",
  currency_symbol: "",
};

const tabAliases: Record<string, Tab> = {
  overview: "overview",
  rooms: "rooms",
  checkin: "checkin",
  "check-in": "checkin",
  "check-in-guest": "checkin",
  "checking-guest": "checkin",
  "active-guests": "active-guests",
  "active-guest": "active-guests",
  inventory: "inventory",
  "live-inventory": "inventory",
  staff: "staff",
  "user-priority": "staff",
  users: "staff",
  settings: "settings",
  help: "help",
  support: "help",
  "help-support": "help",
};

const readTabFromUrl = () => {
  if (typeof window === "undefined") return null;
  const url = new URL(window.location.href);
  const rawTab = url.searchParams.get("tab") || url.hash.replace("#", "");
  return rawTab ? tabAliases[rawTab.toLowerCase()] ?? null : null;
};

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>(() => readTabFromUrl() ?? "overview");
  const [apiStats, setApiStats] = useState<DashboardStats | null>(null);
  const [settings, setSettings] = useState<AppSettings>(emptySettings);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [availableRooms, setAvailableRooms] = useState<Room[]>([]);
  const [activeBookings, setActiveBookings] = useState<ActiveBooking[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [amenities, setAmenities] = useState<string[]>([]);
  const [recentBookings, setRecentBookings] = useState<RecentBooking[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState("");

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers = useMemo(
    () => ({
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    }),
    [token],
  );

  const apiRequest = async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
    const response = await fetch(apiUrl(path), {
      ...options,
      headers: { ...headers, ...(options.headers || {}) },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || "Request failed");
    }
    return response.json();
  };

  const loadAll = async () => {
    const [me, stats, appSettings, roomList, availableRoomList, activeBookingList, inventoryList, staffList, amenityList, bookings, logs] = await Promise.all([
      apiRequest<User>("/users/me"),
      apiRequest<DashboardStats>("/stats"),
      apiRequest<AppSettings>("/settings"),
      apiRequest<Room[]>("/rooms"),
      apiRequest<Room[]>("/rooms/available"),
      apiRequest<ActiveBooking[]>("/bookings/active"),
      apiRequest<InventoryItem[]>("/inventory"),
      apiRequest<Staff[]>("/staff"),
      apiRequest<string[]>("/amenities"),
      apiRequest<RecentBooking[]>("/bookings/recent"),
      apiRequest<ActivityLog[]>("/activity-logs/recent"),
    ]);

    setUser(me);
    setApiStats(stats);
    setSettings({ ...emptySettings, ...appSettings });
    setRooms(roomList);
    setAvailableRooms(availableRoomList);
    setActiveBookings(activeBookingList);
    setInventory(inventoryList);
    setStaff(staffList);
    setAmenities(amenityList);
    setRecentBookings(bookings);
    setActivityLogs(logs);
  };

  useEffect(() => {
    if (!token) {
      window.location.href = "/";
      return;
    }

    void Promise.resolve().then(loadAll).catch(() => {
      localStorage.removeItem("token");
      window.location.href = "/";
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const navigateToTab = useCallback((tab: Tab) => {
    setActiveTab(tab);
    setSearch("");

    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    if (tab === "overview") {
      url.searchParams.delete("tab");
    } else {
      url.searchParams.set("tab", tab);
    }
    window.history.replaceState(null, "", `${url.pathname}${url.search}`);
  }, []);

  if (!user) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
      </div>
    );
  }

  const businessName = settings.business_name || "Hotel PMS";
  const currencySymbol = settings.currency_symbol || "";
  const formatCurrency = (value: number) => `${currencySymbol}${new Intl.NumberFormat().format(value)}`;
  const selectedTab: Tab = user.role !== "admin" && (activeTab === "staff" || activeTab === "settings") ? "overview" : activeTab;
  
  const filteredRooms = rooms.filter((room) => {
    const query = search.trim().toLowerCase();
    return !query || room.name.toLowerCase().includes(query) || (room.amenities || "").toLowerCase().includes(query);
  });

  const filteredInventory = inventory.filter((item) => {
    const query = search.trim().toLowerCase();
    return !query || item.item_name.toLowerCase().includes(query) || item.category.toLowerCase().includes(query);
  });

  const refresh = async (successMessage?: string) => {
    await loadAll();
    if (successMessage) setMessage(successMessage);
  };

  const primaryNavItems = [
    { tab: "overview" as const, label: "Overview", icon: LayoutDashboard },
    { tab: "rooms" as const, label: "Rooms", icon: BedDouble },
    { tab: "checkin" as const, label: "Check-In Guest", icon: UserPlus },
    { tab: "active-guests" as const, label: "Active Guests", icon: CheckCircle2 },
    { tab: "inventory" as const, label: "Live Inventory", icon: Package },
  ];
  const adminNavItems = user.role === "admin" ? [
    { tab: "staff" as const, label: "User Priority", icon: Users },
    { tab: "settings" as const, label: "Settings", icon: Settings },
  ] : [];
  const supportNavItems = [{ tab: "help" as const, label: "Help & Support", icon: LifeBuoy }];
  const visibleNavItems = [...primaryNavItems, ...adminNavItems, ...supportNavItems];

  return (
    <div className="min-h-screen bg-black text-white flex overflow-hidden">
      <aside className="w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col shrink-0">
        <div className="p-6">
          <h1 className="text-xl font-bold text-emerald-500 tracking-tight">{businessName}</h1>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4 overflow-y-auto">
          {primaryNavItems.map((item) => (
            <NavItem key={item.tab} icon={item.icon} label={item.label} active={selectedTab === item.tab} onClick={() => navigateToTab(item.tab)} />
          ))}
          
          {user.role === "admin" && (
            <>
              <div className="pt-4 pb-2 px-4 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Admin</div>
              {adminNavItems.map((item) => (
                <NavItem key={item.tab} icon={item.icon} label={item.label} active={selectedTab === item.tab} onClick={() => navigateToTab(item.tab)} />
              ))}
            </>
          )}
          
          <div className="pt-4 pb-2 px-4 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Support</div>
          {supportNavItems.map((item) => (
            <NavItem key={item.tab} icon={item.icon} label={item.label} active={selectedTab === item.tab} onClick={() => navigateToTab(item.tab)} />
          ))}
        </nav>

        <div className="p-4 mt-auto border-t border-zinc-800">
          <div className="flex items-center gap-3 mb-4 p-2">
            <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center font-bold text-xs">
              {user.username[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{user.username}</p>
              <p className="text-[10px] text-zinc-500 capitalize">{user.role}</p>
            </div>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem("token");
              window.location.href = "/";
            }}
            className="w-full flex items-center gap-2 p-2 text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-lg transition-all"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm">Logout</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-8 bg-black/50 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <select
              value={selectedTab}
              onChange={(event) => navigateToTab(event.target.value as Tab)}
              className="h-10 rounded-lg border border-zinc-800 bg-zinc-950 px-3 text-sm font-semibold text-white outline-none focus:ring-2 focus:ring-emerald-500/50"
            >
              {visibleNavItems.map((item) => (
                <option key={item.tab} value={item.tab}>{item.label}</option>
              ))}
            </select>
            <div className="flex items-center gap-4 bg-zinc-900/50 px-4 py-2 rounded-full border border-zinc-800 w-96 max-w-full">
              <Search className="w-4 h-4 text-zinc-500" />
              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search rooms, guests, items..."
                className="bg-transparent border-none focus:outline-none text-sm w-full"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigateToTab("checkin")}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
            >
              <UserPlus className="w-4 h-4" />
              <span>Check-In</span>
            </button>
          </div>
        </header>

        <div className="p-8 max-w-7xl mx-auto">
          {message && (
            <button onClick={() => setMessage("")} className="mb-6 w-full text-left rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
              {message}
            </button>
          )}

          {selectedTab === "overview" && (
            <Overview
              user={user}
              stats={apiStats}
              bookings={recentBookings}
              logs={activityLogs}
              formatCurrency={formatCurrency}
              showAdmin={user.role === "admin"}
              onNavigate={navigateToTab}
            />
          )}

          {selectedTab === "rooms" && (
            <RoomsPage
              rooms={filteredRooms}
              amenities={amenities}
              formatCurrency={formatCurrency}
              onCreate={async (room) => {
                await apiRequest("/rooms", { method: "POST", body: JSON.stringify(room) });
                await refresh("Room saved successfully.");
              }}
              onDelete={async (id) => {
                await apiRequest(`/rooms/${id}`, { method: "DELETE" });
                await refresh("Room deleted successfully.");
              }}
            />
          )}

          {selectedTab === "checkin" && (
            <CheckInPage
              rooms={availableRooms}
              formatCurrency={formatCurrency}
              onCheckIn={async (booking) => {
                await apiRequest("/bookings", { method: "POST", body: JSON.stringify(booking) });
                await refresh(`${booking.customer_name} checked in successfully.`);
                setActiveTab("active-guests");
              }}
            />
          )}

          {selectedTab === "active-guests" && (
            <ActiveGuestsPage
              bookings={activeBookings}
              formatCurrency={formatCurrency}
              onExtend={async (id, date) => {
                await apiRequest(`/bookings/${id}/extend`, { method: "PUT", body: JSON.stringify({ new_checkout_date: date }) });
                await refresh("Stay extended successfully.");
              }}
              onCheckout={async (id, roomId) => {
                await apiRequest(`/bookings/${id}/checkout?room_id=${roomId}`, { method: "POST" });
                await refresh("Guest checked out successfully.");
              }}
            />
          )}

          {selectedTab === "inventory" && (
            <InventoryPage
              user={user}
              items={filteredInventory}
              activeBookings={activeBookings}
              formatCurrency={formatCurrency}
              onAdjustStock={async (id, amount) => {
                const item = inventory.find(i => i.id === id);
                if (!item) return;
                await apiRequest(`/inventory/${id}/stock`, { method: "PUT", body: JSON.stringify({ new_stock: Math.max(0, item.stock_level + amount) }) });
                await refresh("Stock adjusted.");
              }}
              onSell={async (sale) => {
                await apiRequest("/inventory/sell", { method: "POST", body: JSON.stringify(sale) });
                await refresh("Sale recorded.");
              }}
              onCreate={async (item) => {
                await apiRequest("/inventory", { method: "POST", body: JSON.stringify(item) });
                await refresh("Item added to inventory.");
              }}
            />
          )}

          {selectedTab === "staff" && (
            <StaffPage
              staff={staff}
              onCreate={async (newStaff) => {
                await apiRequest("/staff", { method: "POST", body: JSON.stringify(newStaff) });
                await refresh("Staff account created successfully.");
              }}
              onDelete={async (id) => {
                await apiRequest(`/staff/${id}`, { method: "DELETE" });
                await refresh("Staff account deleted successfully.");
              }}
            />
          )}

          {selectedTab === "settings" && (
            <SettingsPage
              key={`${settings.business_name}-${settings.primary_color}-${settings.caution_fee}-${settings.currency_symbol}-${settings.logo_path}`}
              settings={settings}
              amenities={amenities}
              onSave={async (nextSettings) => {
                const updated = await apiRequest<AppSettings>("/settings", { method: "PUT", body: JSON.stringify(nextSettings) });
                setSettings({ ...emptySettings, ...updated });
                await refresh("Settings updated successfully.");
              }}
              onAddAmenity={async (name) => {
                const updated = await apiRequest<string[]>("/amenities", { method: "POST", body: JSON.stringify({ name }) });
                setAmenities(updated);
                await refresh("Amenity added successfully.");
              }}
              onDeleteAmenity={async (name) => {
                const updated = await apiRequest<string[]>(`/amenities/${encodeURIComponent(name)}`, { method: "DELETE" });
                setAmenities(updated);
                await refresh("Amenity deleted successfully.");
              }}
            />
          )}

          {selectedTab === "help" && (
            <HelpPage
              onSend={async (message) => {
                await apiRequest("/support", { method: "POST", body: JSON.stringify({ message }) });
                setMessage("Message sent successfully! The developer will check the logs.");
              }}
            />
          )}
        </div>
      </main>
    </div>
  );
}

// ... rest of components ...

function Overview({ user, stats, bookings, logs, formatCurrency, showAdmin, onNavigate }: {
  user: User;
  stats: DashboardStats | null;
  bookings: RecentBooking[];
  logs: ActivityLog[];
  formatCurrency: (value: number) => string;
  showAdmin: boolean;
  onNavigate: (tab: Tab) => void;
}) {
  const statCards = [
    { label: "Total Historical", value: stats?.total_bookings?.toString() || "0", icon: TrendingUp, color: "text-emerald-500", bg: "bg-emerald-500/10" },
    { label: "Active Guests", value: stats?.active_guests?.toString() || "0", icon: UserPlus, color: "text-blue-500", bg: "bg-blue-500/10" },
    { label: "Available Rooms", value: stats?.available_rooms?.toString() || "0", icon: BedDouble, color: "text-purple-500", bg: "bg-purple-500/10" },
    { label: "Total Assets", value: stats?.total_rooms?.toString() || "0", icon: Hotel, color: "text-emerald-500", bg: "bg-emerald-500/10" },
  ];
  const actionCards: Array<{ label: string; tab: Tab; icon: React.ComponentType<{ className?: string }>; desc: string }> = [
    { label: "Check-In Guest", tab: "checkin", icon: UserPlus, desc: "Register arrivals" },
    { label: "Active Guests", tab: "active-guests", icon: CheckCircle2, desc: "Manage stays" },
    { label: "Live Inventory", tab: "inventory", icon: Package, desc: "Stock and sales" },
    { label: "Help & Support", tab: "help", icon: LifeBuoy, desc: "Contact support" },
  ];

  if (showAdmin) {
    actionCards.splice(3, 0, { label: "User Priority", tab: "staff", icon: Users, desc: "Admin and staff access" });
  }

  return (
    <>
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight">Welcome back, {user.username}</h2>
        <p className="text-zinc-500 mt-1">Here&apos;s what&apos;s happening at your hotel today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        {statCards.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-2xl hover:border-zinc-700 transition-all cursor-default"
          >
            <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-4", stat.bg)}>
              <stat.icon className={cn("w-5 h-5", stat.color)} />
            </div>
            <p className="text-zinc-500 text-sm font-medium">{stat.label}</p>
            <h3 className="text-2xl font-bold mt-1 tracking-tight">{stat.value}</h3>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 mb-10">
        {actionCards.map((action) => (
          <button
            key={action.label}
            onClick={() => onNavigate(action.tab)}
            className="flex items-center gap-4 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4 text-left transition-all hover:border-emerald-500/60 hover:bg-zinc-900"
          >
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
              <action.icon className="h-5 w-5" />
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-bold text-white">{action.label}</span>
              <span className="block truncate text-xs text-zinc-500">{action.desc}</span>
            </span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Panel className="lg:col-span-2" title="Recent Bookings">
          <BookingsTable bookings={bookings} formatCurrency={formatCurrency} />
        </Panel>
        <Panel title="System Alerts">
          <div className="space-y-4">
            {logs.length > 0 ? logs.map((log) => (
              <AlertItem key={log.id} title={log.action} desc={log.details || log.username} time={log.timestamp} />
            )) : <p className="text-sm text-zinc-500">No activity logs found</p>}
          </div>
        </Panel>
      </div>
    </>
  );
}

function RoomsPage({ rooms, amenities, formatCurrency, onCreate, onDelete }: {
  rooms: Room[];
  amenities: string[];
  formatCurrency: (value: number) => string;
  onCreate: (room: Omit<Room, "id" | "is_available">) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}) {
  const [form, setForm] = useState({ name: "", price: "", caution_fee: "", image_url: "", amenities: "" });
  const [saving, setSaving] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await onCreate({
        name: form.name.trim(),
        price: Number(form.price),
        caution_fee: Number(form.caution_fee),
        image_url: form.image_url.trim(),
        amenities: form.amenities.trim(),
      });
      setForm({ name: "", price: "", caution_fee: "", image_url: "", amenities: "" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      <SectionHeader title="Rooms & Apartments" description="Connected to the existing room database functions." />
      <Panel title="Add Room">
        <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <Input value={form.name} onChange={(value) => setForm({ ...form, name: value })} placeholder="Room name" required />
          <Input value={form.price} onChange={(value) => setForm({ ...form, price: value })} placeholder="Price" type="number" required />
          <Input value={form.caution_fee} onChange={(value) => setForm({ ...form, caution_fee: value })} placeholder="Caution fee" type="number" required />
          <Input value={form.image_url} onChange={(value) => setForm({ ...form, image_url: value })} placeholder="Image path" />
          <button disabled={saving} className="rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold hover:bg-emerald-500 disabled:opacity-60">
            {saving ? "Saving..." : "Save Room"}
          </button>
          <select
            value={form.amenities}
            onChange={(event) => setForm({ ...form, amenities: event.target.value })}
            className="md:col-span-5 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="">No amenity preset selected</option>
            {amenities.map((amenity) => <option key={amenity} value={amenity}>{amenity}</option>)}
          </select>
        </form>
      </Panel>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {rooms.length > 0 ? rooms.map((room) => (
          <div key={room.id} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-bold">{room.name}</h3>
                <p className="text-sm text-zinc-400">{formatCurrency(room.price)} / night</p>
                <p className={cn("mt-2 text-xs font-bold uppercase", room.is_available ? "text-emerald-500" : "text-red-400")}>
                  {room.is_available ? "Available" : "Checked-In"}
                </p>
                {room.amenities && <p className="mt-3 text-sm text-zinc-500">{room.amenities}</p>}
              </div>
              <button onClick={() => onDelete(room.id)} className="rounded-lg bg-red-500/10 p-2 text-red-400 hover:bg-red-500/20">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        )) : <EmptyState text="No rooms found." />}
      </div>
    </div>
  );
}

function StaffPage({ staff, onCreate, onDelete }: {
  staff: Staff[];
  onCreate: (staff: { username: string; password: string; role: string }) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}) {
  const [form, setForm] = useState({ username: "", password: "", role: "staff" });
  const [saving, setSaving] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await onCreate(form);
      setForm({ username: "", password: "", role: "staff" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      <SectionHeader title="User Priority" description="Create users and assign admin or staff access." />
      <Panel title="Add Staff">
        <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Input value={form.username} onChange={(value) => setForm({ ...form, username: value })} placeholder="Username" required />
          <Input value={form.password} onChange={(value) => setForm({ ...form, password: value })} placeholder="Password" type="password" required />
          <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })} className="rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white outline-none">
            <option value="staff">Staff</option>
            <option value="admin">Admin</option>
          </select>
          <button disabled={saving} className="rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold hover:bg-emerald-500 disabled:opacity-60">
            {saving ? "Creating..." : "Create Account"}
          </button>
        </form>
      </Panel>
      <div className="space-y-3">
        {staff.length > 0 ? staff.map((member) => (
          <div key={member.id} className="flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
            <div>
              <p className="font-semibold">{member.username}</p>
              <p className="text-xs uppercase text-zinc-500">{member.role}</p>
            </div>
            {member.id === 1 ? (
              <span className="text-xs text-zinc-500">Master Admin</span>
            ) : (
              <button onClick={() => onDelete(member.id)} className="rounded-lg bg-red-500/10 p-2 text-red-400 hover:bg-red-500/20">
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        )) : <EmptyState text="No staff accounts found." />}
      </div>
    </div>
  );
}

function SettingsPage({ settings, amenities, onSave, onAddAmenity, onDeleteAmenity }: {
  settings: AppSettings;
  amenities: string[];
  onSave: (settings: AppSettings) => Promise<void>;
  onAddAmenity: (name: string) => Promise<void>;
  onDeleteAmenity: (name: string) => Promise<void>;
}) {
  const [form, setForm] = useState(settings);
  const [amenityName, setAmenityName] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await onSave({ ...form, caution_fee: Number(form.caution_fee) });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      <SectionHeader title="System Settings" description="Saves through the existing settings function." />
      <Panel title="Hotel Settings">
        <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input value={form.business_name} onChange={(value) => setForm({ ...form, business_name: value })} placeholder="Hotel name" required />
          <Input value={String(form.caution_fee)} onChange={(value) => setForm({ ...form, caution_fee: Number(value) })} placeholder="Default caution fee" type="number" required />
          <Input value={form.currency_symbol} onChange={(value) => setForm({ ...form, currency_symbol: value })} placeholder="Currency symbol" />
          <Input value={form.logo_path} onChange={(value) => setForm({ ...form, logo_path: value })} placeholder="Logo path" />
          <Input value={form.primary_color} onChange={(value) => setForm({ ...form, primary_color: value })} placeholder="Theme color" />
          <button disabled={saving} className="flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold hover:bg-emerald-500 disabled:opacity-60">
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </Panel>
      <Panel title="Amenities & Facilities">
        <form
          onSubmit={async (event) => {
            event.preventDefault();
            if (!amenityName.trim()) return;
            await onAddAmenity(amenityName.trim());
            setAmenityName("");
          }}
          className="mb-4 flex gap-3"
        >
          <Input value={amenityName} onChange={setAmenityName} placeholder="New amenity name" />
          <button className="rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold hover:bg-emerald-500">Add</button>
        </form>
        <div className="flex flex-wrap gap-2">
          {amenities.length > 0 ? amenities.map((amenity) => (
            <button key={amenity} onClick={() => onDeleteAmenity(amenity)} className="rounded-full border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 hover:border-red-500/50 hover:text-red-300">
              {amenity}
            </button>
          )) : <p className="text-sm text-zinc-500">No amenities found.</p>}
        </div>
      </Panel>
    </div>
  );
}

function BookingsTable({ bookings, formatCurrency }: { bookings: RecentBooking[]; formatCurrency: (value: number) => string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead className="text-xs text-zinc-500 uppercase bg-zinc-950/50">
          <tr>
            <th className="px-6 py-4 font-medium tracking-wider">Guest</th>
            <th className="px-6 py-4 font-medium tracking-wider">Room</th>
            <th className="px-6 py-4 font-medium tracking-wider">Status</th>
            <th className="px-6 py-4 font-medium tracking-wider text-right">Amount</th>
          </tr>
        </thead>
        <tbody className="text-sm divide-y divide-zinc-800/50">
          {bookings.length > 0 ? bookings.map((booking) => (
            <BookingRow
              key={booking.id}
              name={booking.customer_name}
              room={booking.room_name || "Unassigned"}
              status={booking.status}
              amount={formatCurrency((booking.room_price || 0) + (booking.caution_fee || 0))}
            />
          )) : (
            <tr>
              <td className="px-6 py-8 text-center text-zinc-500" colSpan={4}>No bookings found</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function NavItem({ icon: Icon, label, active, onClick }: { icon: React.ComponentType<{ className?: string }>; label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} className={cn("w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium text-sm", active ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/20" : "text-zinc-400 hover:text-white hover:bg-zinc-900")}>
      <Icon className="w-5 h-5" />
      <span>{label}</span>
    </button>
  );
}

function Panel({ title, className, children }: { title: string; className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("bg-zinc-900/50 border border-zinc-800 rounded-2xl overflow-hidden", className)}>
      <div className="p-6 border-b border-zinc-800">
        <h4 className="font-bold">{title}</h4>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div>
      <h2 className="text-3xl font-bold tracking-tight">{title}</h2>
      <p className="text-zinc-500 mt-1">{description}</p>
    </div>
  );
}

function Input({ value, onChange, placeholder, type = "text", required = false }: { value: string; onChange: (value: string) => void; placeholder: string; type?: string; required?: boolean }) {
  return (
    <input
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      type={type}
      required={required}
      className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-emerald-500/50"
    />
  );
}

function BookingRow({ name, room, status, amount }: { name: string; room: string; status: string; amount: string }) {
  return (
    <tr className="hover:bg-zinc-800/30 transition-colors group cursor-default">
      <td className="px-6 py-4"><div className="font-medium text-white">{name}</div></td>
      <td className="px-6 py-4 text-zinc-400">{room}</td>
      <td className="px-6 py-4">
        <span className={cn("px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider", status === "Completed" && "bg-emerald-500/10 text-emerald-500", status === "Pending" && "bg-amber-500/10 text-amber-500", status === "Active" && "bg-blue-500/10 text-blue-500", !["Completed", "Pending", "Active"].includes(status) && "bg-zinc-500/10 text-zinc-400")}>
          {status}
        </span>
      </td>
      <td className="px-6 py-4 font-mono text-zinc-300 text-right">{amount}</td>
    </tr>
  );
}

function AlertItem({ title, desc, time }: { title: string; desc: string; time: string }) {
  return (
    <div className="flex gap-4 p-4 rounded-xl bg-black/40 border border-zinc-800/50 hover:border-zinc-700 transition-all">
      <div className="mt-1 shrink-0 text-emerald-500"><AlertCircle className="w-5 h-5" /></div>
      <div className="min-w-0">
        <h5 className="text-sm font-semibold truncate">{title}</h5>
        <p className="text-xs text-zinc-500 mt-1 line-clamp-2">{desc}</p>
        <p className="text-[10px] text-zinc-600 mt-2 font-mono uppercase tracking-tighter">{time}</p>
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-8 text-center text-sm text-zinc-500">{text}</div>;
}

function CheckInPage({ rooms, formatCurrency, onCheckIn }: {
  rooms: Room[];
  formatCurrency: (value: number) => string;
  onCheckIn: (booking: BookingCreate) => Promise<void>;
}) {
  const [form, setForm] = useState({ customer_name: "", guest_phone: "", room_id: "", adults: "1", children: "0", caution_fee: "" });
  const [saving, setSaving] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.room_id) return;
    setSaving(true);
    try {
      await onCheckIn({
        ...form,
        room_id: Number(form.room_id),
        adults: Number(form.adults),
        children: Number(form.children),
        caution_fee: Number(form.caution_fee),
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <SectionHeader title="Guest Check-In" description="Record a new guest arrival and assign a room." />
      <Panel title="Registration Form">
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider ml-1">Select Room</label>
            <select
              value={form.room_id}
              onChange={(e) => {
                const room = rooms.find(r => r.id === Number(e.target.value));
                setForm({ ...form, room_id: e.target.value, caution_fee: room ? String(room.caution_fee) : "" });
              }}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-emerald-500/50"
              required
            >
              <option value="">Choose an available room...</option>
              {rooms.map(room => (
                <option key={room.id} value={room.id}>{room.name} — {formatCurrency(room.price)}/night</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider ml-1">Guest Name</label>
            <Input value={form.customer_name} onChange={(v) => setForm({ ...form, customer_name: v })} placeholder="Full name of guest" required />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider ml-1">Phone Number</label>
            <Input value={form.guest_phone} onChange={(v) => setForm({ ...form, guest_phone: v })} placeholder="Contact number" required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider ml-1">Adults</label>
              <Input value={form.adults} onChange={(v) => setForm({ ...form, adults: v })} type="number" placeholder="1" required />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider ml-1">Children</label>
              <Input value={form.children} onChange={(v) => setForm({ ...form, children: v })} type="number" placeholder="0" />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider ml-1">Caution Fee Paid</label>
            <Input value={form.caution_fee} onChange={(v) => setForm({ ...form, caution_fee: v })} type="number" placeholder="Amount" required />
          </div>
          <button disabled={saving || !form.room_id} className="w-full rounded-lg bg-emerald-600 px-4 py-4 text-sm font-bold hover:bg-emerald-500 disabled:opacity-60 transition-all mt-4">
            {saving ? "Processing..." : "Complete Check-In"}
          </button>
        </form>
      </Panel>
    </div>
  );
}

function ActiveGuestsPage({ bookings, formatCurrency, onExtend, onCheckout }: {
  bookings: ActiveBooking[];
  formatCurrency: (value: number) => string;
  onExtend: (id: number, date: string) => Promise<void>;
  onCheckout: (id: number, roomId: number) => Promise<void>;
}) {
  const [selectedBooking, setSelectedBooking] = useState<ActiveBooking | null>(null);
  const [newDate, setNewDate] = useState("");

  return (
    <div className="space-y-8">
      <SectionHeader title="Active Guests" description="Currently checked-in guests and stay management." />
      <div className="grid grid-cols-1 gap-4">
        {bookings.length > 0 ? bookings.map((booking) => (
          <div key={booking.booking_id} className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center shrink-0">
                <Users className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <h3 className="text-lg font-bold">{booking.customer_name}</h3>
                <p className="text-sm text-zinc-400">Room: <span className="text-white font-medium">{booking.room_name}</span> ({formatCurrency(booking.room_price)}/night)</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
                  <p className="text-xs text-zinc-500 flex items-center gap-1.5"><Search className="w-3 h-3" /> {booking.guest_phone}</p>
                  <p className="text-xs text-zinc-500 flex items-center gap-1.5"><TrendingUp className="w-3 h-3" /> In: {booking.check_in}</p>
                  {booking.check_out && <p className="text-xs text-amber-400 flex items-center gap-1.5"><AlertCircle className="w-3 h-3" /> Out: {booking.check_out}</p>}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setSelectedBooking(booking);
                  setNewDate(booking.check_out?.split(" ")[0] || new Date().toISOString().split("T")[0]);
                }}
                className="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-sm font-medium transition-all"
              >
                Extend Stay
              </button>
              <button
                onClick={() => onCheckout(booking.booking_id, booking.room_id)}
                className="px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm font-medium transition-all"
              >
                Checkout
              </button>
            </div>
          </div>
        )) : <EmptyState text="No guests are currently checked in." />}
      </div>

      {selectedBooking && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h3 className="text-xl font-bold mb-1">Extend Stay</h3>
            <p className="text-sm text-zinc-500 mb-6">{selectedBooking.customer_name} — {selectedBooking.room_name}</p>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">New Checkout Date</label>
                <Input type="date" value={newDate} onChange={setNewDate} placeholder="YYYY-MM-DD" />
              </div>
              <div className="flex gap-3 pt-4">
                <button onClick={() => setSelectedBooking(null)} className="flex-1 px-4 py-3 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-sm font-bold transition-all">Cancel</button>
                <button
                  onClick={async () => {
                    await onExtend(selectedBooking.booking_id, newDate);
                    setSelectedBooking(null);
                  }}
                  className="flex-1 px-4 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-bold transition-all"
                >
                  Save Date
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function InventoryPage({ user, items, activeBookings, formatCurrency, onAdjustStock, onSell, onCreate }: {
  user: User;
  items: InventoryItem[];
  activeBookings: ActiveBooking[];
  formatCurrency: (value: number) => string;
  onAdjustStock: (id: number, amount: number) => Promise<void>;
  onSell: (sale: SaleCreate) => Promise<void>;
  onCreate: (item: InventoryItemCreate) => Promise<void>;
}) {
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [sellForm, setSellForm] = useState({ quantity: "1", customer_type: "Walk-in", guest_id: "", walkin_name: "", payment_status: "Paid" });
  const [showAdd, setShowAdd] = useState(false);
  const [addForm, setAddForm] = useState({ item_name: "", price: "", stock_level: "", category: "Drinks" });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <SectionHeader title="Bar & Restaurant Inventory" description="Real-time stock tracking and sales point." />
        {user.role === "admin" && (
          <button onClick={() => setShowAdd(true)} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg text-sm font-semibold transition-all">
            <Plus className="w-4 h-4" />
            <span>Add Item</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.length > 0 ? items.map((item) => (
          <div key={item.id} className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 overflow-hidden group">
            <div className="flex justify-between items-start mb-4">
              <span className="px-2 py-0.5 rounded-md bg-zinc-800 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">{item.category}</span>
              <div className={cn("flex items-center gap-1.5 text-xs font-bold", item.stock_level < 5 ? "text-red-400" : "text-emerald-500")}>
                <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", item.stock_level < 5 ? "bg-red-400" : "bg-emerald-500")} />
                Stock: {item.stock_level}
              </div>
            </div>
            <h3 className="text-lg font-bold group-hover:text-emerald-400 transition-colors">{item.item_name}</h3>
            <p className="text-zinc-400 font-mono text-sm mt-1">{formatCurrency(item.price)}</p>
            
            <div className="mt-6 flex items-center justify-between">
              <div className="flex gap-1">
                <button onClick={() => onAdjustStock(item.id, -1)} className="p-1.5 rounded-lg bg-zinc-800 hover:bg-red-500/20 hover:text-red-400 transition-all"><Minus className="w-4 h-4" /></button>
                <button onClick={() => onAdjustStock(item.id, 1)} className="p-1.5 rounded-lg bg-zinc-800 hover:bg-emerald-500/20 hover:text-emerald-400 transition-all"><Plus className="w-4 h-4" /></button>
              </div>
              <button
                disabled={item.stock_level <= 0}
                onClick={() => {
                  setSelectedItem(item);
                  setSellForm({ quantity: "1", customer_type: "Walk-in", guest_id: activeBookings[0]?.booking_id.toString() || "", walkin_name: "", payment_status: "Paid" });
                }}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm font-bold transition-all"
              >
                <ShoppingCart className="w-4 h-4" />
                Sell
              </button>
            </div>
          </div>
        )) : <EmptyState text="No inventory items found." />}
      </div>

      {selectedItem && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h3 className="text-xl font-bold mb-1">Sell Item</h3>
            <p className="text-sm text-zinc-500 mb-6">{selectedItem.item_name} — {formatCurrency(selectedItem.price)}</p>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Quantity</label>
                <Input type="number" value={sellForm.quantity} onChange={(v) => setSellForm({ ...sellForm, quantity: v })} placeholder="1" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Customer Type</label>
                <div className="flex gap-2">
                  <button onClick={() => setSellForm({ ...sellForm, customer_type: "Walk-in", payment_status: "Paid" })} className={cn("flex-1 py-2 rounded-lg border text-sm font-medium transition-all", sellForm.customer_type === "Walk-in" ? "border-emerald-500 bg-emerald-500/10 text-emerald-400" : "border-zinc-800 text-zinc-500 hover:border-zinc-700")}>Walk-in</button>
                  <button disabled={activeBookings.length === 0} onClick={() => setSellForm({ ...sellForm, customer_type: "Guest" })} className={cn("flex-1 py-2 rounded-lg border text-sm font-medium transition-all disabled:opacity-30", sellForm.customer_type === "Guest" ? "border-emerald-500 bg-emerald-500/10 text-emerald-400" : "border-zinc-800 text-zinc-500 hover:border-zinc-700")}>Active Guest</button>
                </div>
              </div>
              {sellForm.customer_type === "Guest" ? (
                <div className="space-y-1">
                  <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Select Guest</label>
                  <select
                    value={sellForm.guest_id}
                    onChange={(e) => setSellForm({ ...sellForm, guest_id: e.target.value })}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-emerald-500/50"
                  >
                    {activeBookings.map(b => (
                      <option key={b.booking_id} value={b.booking_id}>{b.room_name} — {b.customer_name}</option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-1">
                  <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Customer Name (Optional)</label>
                  <Input value={sellForm.walkin_name} onChange={(v) => setSellForm({ ...sellForm, walkin_name: v })} placeholder="e.g. John Doe" />
                </div>
              )}
              <div className="space-y-1">
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Payment Status</label>
                <select
                  value={sellForm.payment_status}
                  onChange={(e) => setSellForm({ ...sellForm, payment_status: e.target.value })}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-emerald-500/50"
                >
                  <option value="Paid">Paid (Instant)</option>
                  {sellForm.customer_type === "Guest" && <option value="Charge to Room">Charge to Room</option>}
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button onClick={() => setSelectedItem(null)} className="flex-1 px-4 py-3 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-sm font-bold transition-all">Cancel</button>
                <button
                  onClick={async () => {
                    const guest = activeBookings.find(b => b.booking_id.toString() === sellForm.guest_id);
                    await onSell({
                      item_id: selectedItem.id,
                      item_name: selectedItem.item_name,
                      price: selectedItem.price,
                      quantity: Number(sellForm.quantity),
                      payment_status: sellForm.payment_status,
                      booking_id: sellForm.customer_type === "Guest" ? Number(sellForm.guest_id) : null,
                      guest_name: sellForm.customer_type === "Guest" ? guest?.customer_name : (sellForm.walkin_name || "Walk-in"),
                    });
                    setSelectedItem(null);
                  }}
                  className="flex-1 px-4 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-bold transition-all"
                >
                  Confirm Sale
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showAdd && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h3 className="text-xl font-bold mb-6">New Inventory Item</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              await onCreate({
                item_name: addForm.item_name.trim(),
                price: Number(addForm.price),
                stock_level: Number(addForm.stock_level),
                category: addForm.category,
              });
              setShowAdd(false);
              setAddForm({ item_name: "", price: "", stock_level: "", category: "Drinks" });
            }} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Item Name</label>
                <Input value={addForm.item_name} onChange={(v) => setAddForm({ ...addForm, item_name: v })} placeholder="e.g. Heineken" required />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Category</label>
                <select value={addForm.category} onChange={(e) => setAddForm({ ...addForm, category: e.target.value })} className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-emerald-500/50">
                  <option value="Drinks">Drinks</option>
                  <option value="Food">Food</option>
                  <option value="Snacks">Snacks</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Price</label>
                  <Input type="number" value={addForm.price} onChange={(v) => setAddForm({ ...addForm, price: v })} placeholder="0.00" required />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Initial Stock</label>
                  <Input type="number" value={addForm.stock_level} onChange={(v) => setAddForm({ ...addForm, stock_level: v })} placeholder="0" required />
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowAdd(false)} className="flex-1 px-4 py-3 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-sm font-bold transition-all">Cancel</button>
                <button type="submit" className="flex-1 px-4 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-bold transition-all">Save Item</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function HelpPage({ onSend }: { onSend: (message: string) => Promise<void> }) {
  const [msg, setMsg] = useState("");
  const [sending, setSending] = useState(false);

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <SectionHeader title="Help & Support" description="Need assistance? Reach out to the developer directly." />
      <Panel title="Contact Information">
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 shrink-0"><LifeBuoy className="w-5 h-5" /></div>
            <div>
              <p className="text-sm font-bold">Email Support</p>
              <p className="text-sm text-zinc-400">hmsupport@oyinoost.com.ng</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 shrink-0"><Search className="w-5 h-5" /></div>
            <div>
              <p className="text-sm font-bold">Phone / WhatsApp</p>
              <p className="text-sm text-zinc-400">+2348030796540</p>
            </div>
          </div>
        </div>
      </Panel>
      <Panel title="Send a Message">
        <div className="space-y-4">
          <textarea
            value={msg}
            onChange={(e) => setMsg(e.target.value)}
            className="w-full h-32 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-emerald-500/50 resize-none"
            placeholder="Describe your issue or request here..."
          />
          <button
            disabled={sending || !msg.trim()}
            onClick={async () => {
              setSending(true);
              try { await onSend(msg); setMsg(""); } finally { setSending(false); }
            }}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-4 text-sm font-bold hover:bg-emerald-500 disabled:opacity-60 transition-all"
          >
            {sending ? "Sending..." : "Send Support Request"}
          </button>
        </div>
      </Panel>
    </div>
  );
}
