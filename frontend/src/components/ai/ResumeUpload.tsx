import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Upload, FileText, Check, AlertCircle, Loader2 } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/components/auth/AuthProvider';

interface UploadStatus {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
}

interface ResumeUploadProps {
  onUploadComplete?: (resumeData: any) => void;
  className?: string;
}

export const ResumeUpload: React.FC<ResumeUploadProps> = ({
  onUploadComplete,
  className = ''
}) => {
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    status: 'idle',
    progress: 0,
    message: ''
  });
  const [dragOver, setDragOver] = useState(false);
  const { profile } = useAuth();
  const { toast } = useToast();

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!profile) {
      toast({
        title: 'Error',
        description: 'You must be logged in to upload a resume.',
        variant: 'destructive',
      });
      return;
    }

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];

    if (!allowedTypes.includes(file.type)) {
      toast({
        title: 'Invalid File Type',
        description: 'Please upload a PDF, DOC, or DOCX file.',
        variant: 'destructive',
      });
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: 'File Too Large',
        description: 'Please upload a file smaller than 10MB.',
        variant: 'destructive',
      });
      return;
    }

    try {
      setUploadStatus({
        status: 'uploading',
        progress: 10,
        message: 'Uploading file...'
      });

      // Upload file to Supabase Storage
      const fileName = `${profile.id}/${Date.now()}-${file.name}`;
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('resumes')
        .upload(fileName, file);

      if (uploadError) {
        throw uploadError;
      }

      setUploadStatus({
        status: 'uploading',
        progress: 30,
        message: 'File uploaded successfully...'
      });

      // Create resume record in database
      const { data: resumeData, error: resumeError } = await supabase
        .from('resumes')
        .insert({
          candidate_id: profile.id,
          filename: file.name,
          file_path: uploadData.path,
          content_type: file.type,
          file_size: file.size,
          parsing_status: 'pending'
        })
        .select()
        .single();

      if (resumeError) {
        throw resumeError;
      }

      setUploadStatus({
        status: 'processing',
        progress: 50,
        message: 'Processing resume with AI...'
      });

      // Extract text content based on file type
      let resumeText = '';
      if (file.type === 'application/pdf') {
        // For PDF files, we'll need to extract text on the server side
        resumeText = `[PDF FILE: ${file.name}]`;
      } else {
        // For DOC/DOCX, we'll also handle this on the server side
        resumeText = `[DOCUMENT FILE: ${file.name}]`;
      }

      // Process with AI
      const { data: aiData, error: aiError } = await supabase.functions.invoke('process-resume', {
        body: {
          resumeText: resumeText,
          candidateId: profile.id
        }
      });

      if (aiError) {
        throw aiError;
      }

      setUploadStatus({
        status: 'completed',
        progress: 100,
        message: 'Resume processed successfully!'
      });

      toast({
        title: 'Success!',
        description: 'Your resume has been uploaded and analyzed.',
      });

      if (onUploadComplete) {
        onUploadComplete({ ...resumeData, analysis: aiData.analysis });
      }

    } catch (error) {
      console.error('Resume upload error:', error);
      setUploadStatus({
        status: 'error',
        progress: 0,
        message: 'Failed to process resume. Please try again.'
      });

      toast({
        title: 'Upload Failed',
        description: 'There was an error processing your resume. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const getStatusIcon = () => {
    switch (uploadStatus.status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-primary" />;
      case 'completed':
        return <Check className="h-5 w-5 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-destructive" />;
      default:
        return <Upload className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = () => {
    switch (uploadStatus.status) {
      case 'completed':
        return 'text-green-600';
      case 'error':
        return 'text-destructive';
      case 'uploading':
      case 'processing':
        return 'text-primary';
      default:
        return 'text-muted-foreground';
    }
  };

  const isProcessing = uploadStatus.status === 'uploading' || uploadStatus.status === 'processing';

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Resume Upload & Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragOver
              ? 'border-primary bg-primary/5'
              : uploadStatus.status === 'completed'
              ? 'border-green-300 bg-green-50'
              : uploadStatus.status === 'error'
              ? 'border-destructive bg-destructive/5'
              : 'border-border hover:border-primary/50'
          }`}
          onDragEnter={handleDragIn}
          onDragLeave={handleDragOut}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center gap-4">
            {getStatusIcon()}
            
            <div>
              <p className={`font-medium ${getStatusColor()}`}>
                {uploadStatus.status === 'idle' && 'Drop your resume here or click to browse'}
                {uploadStatus.status !== 'idle' && uploadStatus.message}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {uploadStatus.status === 'idle' && 'Supports PDF, DOC, and DOCX files up to 10MB'}
              </p>
            </div>

            {isProcessing && (
              <div className="w-full max-w-xs">
                <Progress value={uploadStatus.progress} className="w-full" />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>Processing...</span>
                  <span>{uploadStatus.progress}%</span>
                </div>
              </div>
            )}

            {uploadStatus.status === 'completed' && (
              <Badge variant="secondary" className="bg-green-100 text-green-700">
                Analysis Complete
              </Badge>
            )}

            {uploadStatus.status === 'idle' && (
              <input
                type="file"
                onChange={handleFileSelect}
                accept=".pdf,.doc,.docx"
                className="hidden"
                id="resume-upload"
                disabled={isProcessing}
              />
            )}
          </div>
        </div>

        {uploadStatus.status === 'idle' && (
          <div className="flex justify-center mt-4">
            <Button variant="outline" asChild>
              <label htmlFor="resume-upload" className="cursor-pointer">
                <Upload className="h-4 w-4 mr-2" />
                Choose File
              </label>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};