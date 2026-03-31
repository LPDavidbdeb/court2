import React, { useEffect, useState } from 'react';
import { protagonistService } from '../services/protagonistService';
import type { Protagonist, ProtagonistCreate } from '../types/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { UserPlus, Pencil, Trash2, Link, Mail } from 'lucide-react';

const ProtagonistDirectory: React.FC = () => {
  const [protagonists, setProtagonists] = useState<Protagonist[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<ProtagonistCreate>({
    first_name: '',
    last_name: '',
    role: '',
    linkedin_url: '',
    emails: []
  });

  const fetchProtagonists = async () => {
    try {
      setLoading(true);
      const data = await protagonistService.list();
      setProtagonists(data);
    } catch (error) {
      console.error('Error fetching protagonists:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProtagonists();
  }, []);

  const handleEdit = (p: Protagonist) => {
    setEditingId(p.id);
    setFormData({
      first_name: p.first_name,
      last_name: p.last_name || '',
      role: p.role,
      linkedin_url: p.linkedin_url || '',
      emails: p.emails
    });
    setIsOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this protagonist?')) {
      await protagonistService.delete(id);
      fetchProtagonists();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await protagonistService.update(editingId, formData);
      } else {
        await protagonistService.create(formData);
      }
      setIsOpen(false);
      setEditingId(null);
      setFormData({ first_name: '', last_name: '', role: '', linkedin_url: '', emails: [] });
      fetchProtagonists();
    } catch (error) {
      console.error('Error saving protagonist:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Protagonist Directory</h1>
          <p className="text-muted-foreground">Manage legal actors, witnesses, and stakeholders.</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingId(null); setFormData({ first_name: '', last_name: '', role: '', linkedin_url: '', emails: [] }); }}>
              <UserPlus className="mr-2 h-4 w-4" /> Add Protagonist
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingId ? 'Edit Protagonist' : 'New Protagonist'}</DialogTitle>
              <DialogDescription>Enter details for the case participant.</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 pt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">First Name</label>
                  <Input 
                    value={formData.first_name} 
                    onChange={e => setFormData({...formData, first_name: e.target.value})} 
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Last Name</label>
                  <Input 
                    value={formData.last_name} 
                    onChange={e => setFormData({...formData, last_name: e.target.value})} 
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Role</label>
                <Input 
                  value={formData.role} 
                  onChange={e => setFormData({...formData, role: e.target.value})} 
                  placeholder="e.g. Witness, Lawyer, Defendant"
                  required 
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">LinkedIn URL</label>
                <Input 
                  value={formData.linkedin_url} 
                  onChange={e => setFormData({...formData, linkedin_url: e.target.value})} 
                  placeholder="https://linkedin.com/in/..."
                />
              </div>
              <DialogFooter>
                <Button type="submit">{editingId ? 'Update' : 'Create'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Contacts</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={4} className="text-center py-10">Loading...</TableCell></TableRow>
              ) : protagonists.length === 0 ? (
                <TableRow><TableCell colSpan={4} className="text-center py-10 text-muted-foreground">No protagonists found.</TableCell></TableRow>
              ) : protagonists.map(p => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">
                    {p.first_name} {p.last_name}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{p.role}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {p.linkedin_url && (
                        <a href={p.linkedin_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800">
                          <Link className="h-4 w-4" />
                        </a>
                      )}
                      {p.emails.length > 0 && (
                        <div className="flex items-center text-slate-500 text-xs">
                          <Mail className="h-3 w-3 mr-1" /> {p.emails[0].email_address}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(p)}><Pencil className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={() => handleDelete(p.id)}><Trash2 className="h-4 w-4" /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProtagonistDirectory;
