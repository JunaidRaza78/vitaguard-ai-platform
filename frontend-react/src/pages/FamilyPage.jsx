import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Users, Plus, UserPlus, Link2, Trash2, Crown, ChevronRight } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import Badge from '@/components/ui/Badge'
import Select from '@/components/ui/Select'
import EmptyState from '@/components/ui/EmptyState'
import { getInitials } from '@/lib/utils'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

export default function FamilyPage() {
  const [families, setFamilies] = useState([])
  const [selectedFamily, setSelectedFamily] = useState(null)
  const [members, setMembers] = useState([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAddMemberModal, setShowAddMemberModal] = useState(false)
  const [showRelationshipModal, setShowRelationshipModal] = useState(false)
  const [familyTree, setFamilyTree] = useState(null)
  const [loading, setLoading] = useState(true)
  const [familyName, setFamilyName] = useState('')
  const [memberEmail, setMemberEmail] = useState('')
  const [relationship, setRelationship] = useState({ member1: '', member2: '', type: 'parent' })

  useEffect(() => {
    loadFamilies()
  }, [])

  const loadFamilies = async () => {
    try {
      const { data } = await api.get('/api/v1/families/me')
      setFamilies(data.families || data || [])
      if (data.families?.length > 0 || data.length > 0) {
        const first = data.families?.[0] || data[0]
        selectFamily(first)
      }
    } catch {
      // graceful fallback
    } finally {
      setLoading(false)
    }
  }

  const selectFamily = async (family) => {
    setSelectedFamily(family)
    const fid = family.familyId || family.family_id || family.id
    try {
      const [membersRes, treeRes] = await Promise.allSettled([
        api.get(`/api/v1/families/${fid}/members`),
        api.get(`/api/v1/families/${fid}/tree`),
      ])
      if (membersRes.status === 'fulfilled') setMembers(membersRes.value.data.members || membersRes.value.data || [])
      if (treeRes.status === 'fulfilled') setFamilyTree(treeRes.value.data)
    } catch {}
  }

  const createFamily = async () => {
    if (!familyName.trim()) return
    try {
      await api.post('/api/v1/families', { name: familyName })
      toast.success('Family created')
      setShowCreateModal(false)
      setFamilyName('')
      loadFamilies()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create family')
    }
  }

  const addMember = async () => {
    if (!memberEmail.trim() || !selectedFamily) return
    try {
      const fid = selectedFamily.familyId || selectedFamily.family_id || selectedFamily.id
      await api.post(`/api/v1/families/${fid}/members`, { email: memberEmail })
      toast.success('Member added')
      setShowAddMemberModal(false)
      setMemberEmail('')
      selectFamily(selectedFamily)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add member')
    }
  }

  const removeMember = async (memberId) => {
    if (!selectedFamily) return
    try {
      const fid = selectedFamily.familyId || selectedFamily.family_id || selectedFamily.id
      await api.delete(`/api/v1/families/${fid}/members/${memberId}`)
      toast.success('Member removed')
      selectFamily(selectedFamily)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to remove member')
    }
  }

  const createRelationship = async () => {
    if (!selectedFamily) return
    try {
      const fid = selectedFamily.familyId || selectedFamily.family_id || selectedFamily.id
      await api.post(`/api/v1/families/${fid}/relationships`, relationship)
      toast.success('Relationship created')
      setShowRelationshipModal(false)
      selectFamily(selectedFamily)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create relationship')
    }
  }

  const avatarColors = [
    'from-cyan-500 to-blue-500',
    'from-violet-500 to-fuchsia-500',
    'from-emerald-500 to-teal-500',
    'from-rose-500 to-pink-500',
    'from-amber-500 to-orange-500',
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Family Management</h2>
          <p className="text-sm text-white/40">Manage your family groups and relationships</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} size="sm">
          <Plus className="w-4 h-4" />
          Create Family
        </Button>
      </div>

      {/* Family Cards */}
      {families.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {families.map((family, i) => (
            <motion.div
              key={family.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <GlassCard
                className={`cursor-pointer ${selectedFamily?.id === family.id ? 'glow-cyan border-cyan-500/30' : ''}`}
                onClick={() => selectFamily(family)}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-cyan-400" />
                    <h3 className="font-semibold text-white">{family.name}</h3>
                  </div>
                  <ChevronRight className="w-4 h-4 text-white/30" />
                </div>
                <div className="flex -space-x-2">
                  {(family.members || []).slice(0, 5).map((m, j) => (
                    <div
                      key={j}
                      className={`w-8 h-8 rounded-full bg-gradient-to-br ${avatarColors[j % avatarColors.length]} flex items-center justify-center text-[10px] font-bold text-white border-2 border-dark-800`}
                    >
                      {getInitials(m.first_name, m.last_name)}
                    </div>
                  ))}
                </div>
                <p className="text-xs text-white/40 mt-2">
                  {family.member_count || family.members?.length || 0} members
                </p>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      ) : !loading ? (
        <EmptyState
          icon={Users}
          title="No families yet"
          description="Create a family group to manage health data together"
          action={
            <Button onClick={() => setShowCreateModal(true)} size="sm">
              <Plus className="w-4 h-4" /> Create Family
            </Button>
          }
        />
      ) : null}

      {/* Selected Family Details */}
      {selectedFamily && (
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Crown className="w-4 h-4 text-amber-400" />
              {selectedFamily.name} - Members
            </h3>
            <div className="flex gap-2">
              <Button onClick={() => setShowAddMemberModal(true)} variant="ghost" size="sm">
                <UserPlus className="w-4 h-4" /> Add
              </Button>
              <Button onClick={() => setShowRelationshipModal(true)} variant="ghost" size="sm">
                <Link2 className="w-4 h-4" /> Relationship
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            {members.map((member, i) => (
              <motion.div
                key={member.id || i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-3 glass rounded-xl p-3"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${avatarColors[i % avatarColors.length]} flex items-center justify-center text-sm font-bold text-white`}>
                  {getInitials(member.name?.split(' ')[0], member.name?.split(' ')[1])}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">
                    {member.name || member.email || 'Unknown'}
                  </p>
                  <p className="text-xs text-white/40">{member.email}</p>
                </div>
                {member.role && <Badge color="violet">{member.role}</Badge>}
                <button
                  onClick={() => removeMember(member.userId || member.user_id || member.id)}
                  className="p-1.5 rounded-lg hover:bg-rose-500/10 text-white/30 hover:text-rose-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </motion.div>
            ))}
          </div>

          {/* Family Tree Visualization */}
          {familyTree && (
            <div className="mt-6 pt-4 border-t border-white/10">
              <h4 className="text-sm font-medium text-white/60 mb-3">Family Tree</h4>
              <div className="glass rounded-xl p-6 min-h-[200px] flex items-center justify-center">
                <div className="text-center">
                  <Users className="w-8 h-8 text-cyan-400/40 mx-auto mb-2" />
                  <p className="text-xs text-white/40">
                    {familyTree.nodes?.length || 0} members connected
                  </p>
                  {/* Interactive tree would go here with SVG/Canvas */}
                  <div className="flex flex-wrap justify-center gap-3 mt-4">
                    {(familyTree.nodes || []).map((node, i) => (
                      <div key={i} className="flex flex-col items-center">
                        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${avatarColors[i % avatarColors.length]} flex items-center justify-center text-sm font-bold text-white`}>
                          {getInitials(node.name?.split(' ')[0], node.name?.split(' ')[1])}
                        </div>
                        <p className="text-[10px] text-white/50 mt-1">{node.name?.split(' ')[0] || node.email}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </GlassCard>
      )}

      {/* Create Family Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Family">
        <div className="space-y-4">
          <Input
            label="Family Name"
            placeholder="e.g., Smith Family"
            value={familyName}
            onChange={(e) => setFamilyName(e.target.value)}
          />
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setShowCreateModal(false)} className="flex-1">Cancel</Button>
            <Button onClick={createFamily} className="flex-1">Create</Button>
          </div>
        </div>
      </Modal>

      {/* Add Member Modal */}
      <Modal isOpen={showAddMemberModal} onClose={() => setShowAddMemberModal(false)} title="Add Member">
        <div className="space-y-4">
          <Input
            label="Member Email"
            type="email"
            placeholder="member@example.com"
            value={memberEmail}
            onChange={(e) => setMemberEmail(e.target.value)}
          />
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setShowAddMemberModal(false)} className="flex-1">Cancel</Button>
            <Button onClick={addMember} className="flex-1">Add Member</Button>
          </div>
        </div>
      </Modal>

      {/* Relationship Modal */}
      <Modal isOpen={showRelationshipModal} onClose={() => setShowRelationshipModal(false)} title="Create Relationship">
        <div className="space-y-4">
          <Select
            label="Member 1"
            options={members.map(m => ({ value: m.userId || m.user_id || m.id, label: m.name || m.email || 'Unknown' }))}
            value={relationship.member1}
            onChange={(e) => setRelationship(prev => ({ ...prev, member1: e.target.value }))}
          />
          <Select
            label="Relationship Type"
            options={[
              { value: 'parent', label: 'Parent of' },
              { value: 'spouse', label: 'Spouse of' },
              { value: 'sibling', label: 'Sibling of' },
              { value: 'child', label: 'Child of' },
            ]}
            value={relationship.type}
            onChange={(e) => setRelationship(prev => ({ ...prev, type: e.target.value }))}
          />
          <Select
            label="Member 2"
            options={members.map(m => ({ value: m.userId || m.user_id || m.id, label: m.name || m.email || 'Unknown' }))}
            value={relationship.member2}
            onChange={(e) => setRelationship(prev => ({ ...prev, member2: e.target.value }))}
          />
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setShowRelationshipModal(false)} className="flex-1">Cancel</Button>
            <Button onClick={createRelationship} className="flex-1">Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
