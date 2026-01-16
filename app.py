import React, { useState, useEffect, useMemo } from 'react';
import { LogOut, History, Trash2, LayoutDashboard, Settings as SettingsIcon, Droplets, Footprints, Waves } from 'lucide-react';
import { User, WaterRecord, AuthState, WaterPurpose } from './types';
import { api } from './services/api';
import { PURPOSES, formatWater } from './constants';
import WaterCircle from './components/WaterCircle';
import IntakeButtons from './components/IntakeButtons';
import StatsDashboard from './components/StatsDashboard';
import Achievements from './components/Achievements';
import AuthForms from './components/AuthForms';
import GoalSettings from './components/GoalSettings';

const App: React.FC = () => {
  const [auth, setAuth] = useState<AuthState>({ user: null, token: null, loading: true });
  const [records, setRecords] = useState<WaterRecord[]>([]);
  const [activeTab, setActiveTab] = useState<'dash' | 'stats' | 'settings'>('dash');

  useEffect(() => {
    const initialize = async () => {
      const storedToken = localStorage.getItem('aqua_track_token');
      const storedUser = localStorage.getItem('aqua_track_user');
      
      if (storedToken && storedUser) {
        const user = JSON.parse(storedUser);
        setAuth({ user, token: storedToken, loading: false });
        const fetchedRecords = await api.getRecords(user.id, storedToken);
        setRecords(fetchedRecords);
      } else {
        setAuth(prev => ({ ...prev, loading: false }));
      }
    };
    initialize();
  }, []);

  const handleLogin = async (email: string) => {
    const { user, token } = await api.login(email);
    setAuth({ user, token, loading: false });
    localStorage.setItem('aqua_track_token', token);
    localStorage.setItem('aqua_track_user', JSON.stringify({ ...user, utilityLimit: 150000 }));
    const fetchedRecords = await api.getRecords(user.id, token);
    setRecords(fetchedRecords);
  };

  const handleLogout = () => {
    localStorage.removeItem('aqua_track_token');
    localStorage.removeItem('aqua_track_user');
    setAuth({ user: null, token: null, loading: false });
    setRecords([]);
  };

  const addIntake = async (amount: number, purpose: WaterPurpose) => {
    if (!auth.user || !auth.token) return;
    const newRecord = await api.addRecord(amount, purpose, auth.user.id, auth.token);
    setRecords(prev => [...prev, newRecord]);
  };

  const clearToday = async () => {
    if (!auth.user || !auth.token) return;
    if (confirm('Clear today\'s logs?')) {
      await api.clearRecords(auth.user.id, auth.token);
      setRecords([]);
    }
  };

  const updateProfile = async (updatedUser: User) => {
    if (!auth.token) return;
    const result = await api.updateUser(updatedUser, auth.token);
    setAuth(prev => ({ ...prev, user: result }));
    localStorage.setItem('aqua_track_user', JSON.stringify(result));
  };

  const todayStr = new Date().toISOString().split('T')[0];
  const todayRecords = records.filter(r => r.timestamp.startsWith(todayStr));
  const hydrationTotal = todayRecords.filter(r => r.purpose === 'hydration').reduce((sum, r) => sum + r.amount, 0);
  const footprintTotal = todayRecords.reduce((sum, r) => sum + r.amount, 0);

  const unlockedAchievements = useMemo(() => {
    const ids = [];
    if (records.length > 0) ids.push('1');
    if (auth.user && hydrationTotal >= auth.user.dailyGoal * 0.5) ids.push('2');
    if (auth.user && hydrationTotal >= auth.user.dailyGoal) ids.push('3');
    return ids;
  }, [records, hydrationTotal, auth.user]);

  if (auth.loading) return (
    <div className="h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  if (!auth.user) return <AuthForms onLogin={handleLogin} />;

  return (
    <div className="max-w-xl mx-auto px-4 py-8 pb-32">
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-2">
          <Waves className="w-7 h-7 text-blue-500" />
          <h1 className="text-xl font-bold tracking-tight">AquaTrack</h1>
        </div>
        <button onClick={handleLogout} className="p-2 text-slate-500 hover:text-white transition-colors">
          <LogOut size={20} />
        </button>
      </header>

      <main className="space-y-6">
        {activeTab === 'dash' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass p-6 text-center">
                <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-4 block">Goal Progress</span>
                <WaterCircle current={hydrationTotal} goal={auth.user.dailyGoal} />
              </div>
              <div className="glass p-6 flex flex-col justify-center items-center">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 block">Total Usage</span>
                <div className="text-4xl font-extrabold text-white mb-1">{formatWater(footprintTotal)}</div>
                <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
                  <Footprints size={12} /> Daily footprint
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Quick Log</h3>
              <IntakeButtons onAdd={addIntake} />
            </div>

            <Achievements unlockedIds={unlockedAchievements} />

            <div className="glass p-5">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <History size={16} className="text-blue-500" /> Recent Activity
                </h3>
                <button onClick={clearToday} className="text-slate-600 hover:text-red-500"><Trash2 size={14}/></button>
              </div>
              <div className="space-y-2 max-h-40 overflow-y-auto no-scrollbar">
                {todayRecords.length === 0 ? (
                  <p className="text-xs text-slate-600 text-center py-4">No logs yet today.</p>
                ) : (
                  todayRecords.slice().reverse().map(record => (
                    <div key={record.id} className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-bold">{formatWater(record.amount)}</span>
                        <span className="text-[10px] font-bold text-blue-400/80 uppercase">{record.purpose}</span>
                      </div>
                      <span className="text-[10px] text-slate-600">
                        {new Date(record.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}

        {activeTab === 'stats' && <StatsDashboard records={records} />}
        {activeTab === 'settings' && <GoalSettings user={auth.user} onUpdate={updateProfile} />}
      </main>

      <nav className="fixed bottom-6 left-1/2 -translate-x-1/2 glass px-8 py-4 flex items-center gap-10 z-50">
        <button onClick={() => setActiveTab('dash')} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'dash' ? 'text-blue-500' : 'text-slate-500'}`}>
          <LayoutDashboard size={20} />
          <span className="text-[9px] font-bold uppercase tracking-tighter">Dash</span>
        </button>
        <button onClick={() => setActiveTab('stats')} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'stats' ? 'text-blue-500' : 'text-slate-500'}`}>
          <History size={20} />
          <span className="text-[9px] font-bold uppercase tracking-tighter">Stats</span>
        </button>
        <button onClick={() => setActiveTab('settings')} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'settings' ? 'text-blue-500' : 'text-slate-500'}`}>
          <SettingsIcon size={20} />
          <span className="text-[9px] font-bold uppercase tracking-tighter">Setup</span>
        </button>
      </nav>
    </div>
  );
};

export default App;