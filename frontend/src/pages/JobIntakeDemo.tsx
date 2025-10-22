import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { CheckCircle2, ClipboardList, Mail, Sparkles, TrendingUp } from 'lucide-react';

type JobProfile = {
  title: string;
  requiredSkills: string[];
  niceToHaveSkills: string[];
  minYearsExperience?: number;
  locations: string[];
  salaryHint?: string;
};

type CandidateProfile = {
  name: string;
  skills: string[];
  yearsExperience?: number;
};

type AuditLog = {
  id: string;
  action: string;
  details: string;
  timestamp: Date;
};

function extractJobProfile(text: string): JobProfile {
  const lower = text.toLowerCase();
  const titleMatch = text.match(/title[:\-]\s*(.+)/i);
  const title = titleMatch ? titleMatch[1].trim() : (text.split(/\n|\./)[0] || 'Job Role').trim();

  const skillRegex = /(skills|required skills|requirements)[:\-]([^\n]+)/i;
  const niceRegex = /(nice to have|preferred)[:\-]([^\n]+)/i;
  const locRegex = /(location|locations)[:\-]([^\n]+)/i;
  const expRegex = /(\d+)\s*\+?\s*(years|yrs)/i;
  const salaryRegex = /(ctc|salary|compensation)[:\-]([^\n]+)/i;

  const requiredSkills = (skillRegex.exec(text)?.[2] || '')
    .split(/,|•|\u2022|\||\/|\n| and /i)
    .map(s => s.trim())
    .filter(Boolean);

  const niceToHaveSkills = (niceRegex.exec(text)?.[2] || '')
    .split(/,|•|\u2022|\||\/|\n| and /i)
    .map(s => s.trim())
    .filter(Boolean);

  const locations = (locRegex.exec(text)?.[2] || '')
    .split(/,|\||\//)
    .map(s => s.trim())
    .filter(Boolean);

  const yearsMatch = expRegex.exec(lower);
  const minYearsExperience = yearsMatch ? parseInt(yearsMatch[1], 10) : undefined;
  const salaryHint = salaryRegex.exec(text)?.[2]?.trim();

  return { title, requiredSkills, niceToHaveSkills, minYearsExperience, locations, salaryHint };
}

function scoreCandidateFit(job: JobProfile, candidate: CandidateProfile): { score: number; reasons: string[] } {
  const reasons: string[] = [];
  if (!candidate.skills.length) return { score: 0, reasons: ['No skills provided'] };

  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9+#.]/g, ' ').replace(/\s+/g, ' ').trim();
  const jobReq = job.requiredSkills.map(norm);
  const jobNice = job.niceToHaveSkills.map(norm);
  const cand = new Set(candidate.skills.map(norm));

  let score = 0;
  let reqMatches = 0;
  for (const r of jobReq) {
    if (r && Array.from(cand).some(s => s.includes(r) || r.includes(s))) {
      reqMatches += 1;
      score += 20; // weight required skills
    }
  }
  if (reqMatches) reasons.push(`${reqMatches} required skill(s) matched`);

  let niceMatches = 0;
  for (const n of jobNice) {
    if (n && Array.from(cand).some(s => s.includes(n) || n.includes(s))) {
      niceMatches += 1;
      score += 8; // weight nice-to-have
    }
  }
  if (niceMatches) reasons.push(`${niceMatches} nice-to-have skill(s) matched`);

  if (job.minYearsExperience && candidate.yearsExperience) {
    if (candidate.yearsExperience >= job.minYearsExperience) {
      score += 12;
      reasons.push(`Experience meets threshold (${candidate.yearsExperience}y)`);
    } else {
      reasons.push(`Experience below threshold (${candidate.yearsExperience}y < ${job.minYearsExperience}y)`);
    }
  }

  score = Math.min(100, Math.max(0, score));
  return { score, reasons };
}

const JobIntakeDemo: React.FC = () => {
  const [jdText, setJdText] = useState('Title: Full Stack Developer\nSkills: React, Node.js, TypeScript, PostgreSQL\nNice to have: Docker, AWS\nLocations: Remote, Bangalore\nExperience: 3+ years\nSalary: 12–20 LPA');
  const [candidate, setCandidate] = useState<CandidateProfile>({
    name: 'Sample Candidate',
    skills: ['React', 'TypeScript', 'Node.js', 'Docker'],
    yearsExperience: 4,
  });
  const [audit, setAudit] = useState<AuditLog[]>([]);

  const jobProfile = useMemo(() => extractJobProfile(jdText), [jdText]);
  const scoring = useMemo(() => scoreCandidateFit(jobProfile, candidate), [jobProfile, candidate]);

  const addAudit = (action: string, details: string) => {
    setAudit(prev => [{ id: crypto.randomUUID(), action, details, timestamp: new Date() }, ...prev]);
  };

  const handleParse = () => {
    addAudit('job_profile_parsed', `Parsed job: ${jobProfile.title}`);
  };

  const handleAutoDecision = () => {
    const score = scoring.score;
    const decision = score >= 80 ? 'proceed_to_interview' : score >= 50 ? 'needs_review' : 'reject_draft';
    addAudit('decision_made', `Decision: ${decision} (score ${score})`);
  };

  const handleEmailDraft = () => {
    const greeting = scoring.score >= 80 ? 'Hi' : 'Hello';
    const body = scoring.score >= 80
      ? `We reviewed your profile for ${jobProfile.title}. You seem like a great fit. Would you be available for a quick call this week?`
      : `Thanks for your interest in ${jobProfile.title}. We are reviewing profiles and will revert soon.`;
    const draft = `${greeting} ${candidate.name},\n\n${body}\n\nRegards,\nRecruitment Team`;
    navigator.clipboard?.writeText(draft).catch(() => {});
    addAudit('email_drafted', `Draft copied to clipboard (score ${scoring.score})`);
  };

  return (
    <div className="container mx-auto p-4 md:p-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><ClipboardList className="h-5 w-5" /> Job Intake Parser</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea value={jdText} onChange={e => setJdText(e.target.value)} rows={10} />
            <div className="flex gap-2">
              <Button onClick={handleParse}><Sparkles className="h-4 w-4 mr-2" /> Parse Job</Button>
              <Button variant="outline" onClick={handleAutoDecision}><TrendingUp className="h-4 w-4 mr-2" /> Decide Action</Button>
              <Button variant="secondary" onClick={handleEmailDraft}><Mail className="h-4 w-4 mr-2" /> Draft Email</Button>
            </div>
            <Separator />
            <div>
              <h3 className="font-semibold mb-2">Structured Job Profile</h3>
              <div className="space-y-2 text-sm">
                <div><span className="font-medium">Title:</span> {jobProfile.title}</div>
                <div className="flex flex-wrap gap-2">
                  <span className="font-medium mt-1">Required:</span>
                  {jobProfile.requiredSkills.length ? jobProfile.requiredSkills.map(s => (
                    <Badge key={s} variant="secondary">{s}</Badge>
                  )) : <span className="text-muted-foreground">None detected</span>}
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="font-medium mt-1">Nice to have:</span>
                  {jobProfile.niceToHaveSkills.length ? jobProfile.niceToHaveSkills.map(s => (
                    <Badge key={s} variant="outline">{s}</Badge>
                  )) : <span className="text-muted-foreground">None</span>}
                </div>
                <div>
                  <span className="font-medium">Experience:</span> {jobProfile.minYearsExperience ?? '—'} years
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="font-medium mt-1">Locations:</span>
                  {jobProfile.locations.length ? jobProfile.locations.map(l => (
                    <Badge key={l}>{l}</Badge>
                  )) : <span className="text-muted-foreground">Not specified</span>}
                </div>
                {jobProfile.salaryHint && (
                  <div><span className="font-medium">Salary:</span> {jobProfile.salaryHint}</div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><CheckCircle2 className="h-5 w-5" /> Fit Scoring (Demo)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input value={candidate.name} onChange={e => setCandidate(c => ({ ...c, name: e.target.value }))} placeholder="Candidate name" />
              <Input value={candidate.skills.join(', ')} onChange={e => setCandidate(c => ({ ...c, skills: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }))} placeholder="Skills (comma separated)" />
              <Input type="number" value={candidate.yearsExperience ?? ''} onChange={e => setCandidate(c => ({ ...c, yearsExperience: e.target.value ? parseInt(e.target.value, 10) : undefined }))} placeholder="Years of experience" />
              <div className="flex items-center gap-3">
                <div className="text-3xl font-bold">{Math.round(scoring.score)}%</div>
                <div className="text-sm text-muted-foreground">{scoring.reasons.join(' · ') || 'No reasons'}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Audit Log</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                {audit.length === 0 && <div className="text-muted-foreground">No actions yet</div>}
                {audit.map(a => (
                  <div key={a.id} className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium">{a.action}</div>
                      <div className="text-muted-foreground">{a.details}</div>
                    </div>
                    <div className="text-xs text-muted-foreground">{a.timestamp.toLocaleTimeString()}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default JobIntakeDemo;


