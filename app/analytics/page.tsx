"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { getAllStudentsWithRisk, getDropoutRisk } from "@/lib/api";
import { StudentWithRisk } from "@/lib/types";

export default function AnalyticsPage() {
  const [students, setStudents] = useState<StudentWithRisk[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<StudentWithRisk | null>(null);
  const [riskDetails, setRiskDetails] = useState<{ risk_score: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStudents();
  }, []);

  const loadStudents = async () => {
    try {
      const data = await getAllStudentsWithRisk();
      setStudents(data);
    } catch (error) {
      console.error("Failed to load students:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadStudentRisk = async (studentId: number) => {
    try {
      const data = await getDropoutRisk(studentId);
      setRiskDetails(data);
    } catch (error) {
      console.error("Failed to load risk details:", error);
    }
  };

  const getRiskColor = (risk?: number) => {
    if (!risk) return "default";
    if (risk < 40) return "default";
    if (risk < 70) return "secondary";
    return "destructive";
  };

  const getRiskLabel = (risk?: number) => {
    if (!risk) return "Unknown";
    if (risk < 40) return "Low Risk";
    if (risk < 70) return "Medium Risk";
    return "High Risk";
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor student progress and dropout risk
          </p>
        </div>
        <Button onClick={loadStudents} variant="outline">
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-bold">{students.length}</div>
          <div className="text-sm text-muted-foreground">Total Students</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-green-600">
            {students.filter((s) => (s.dropout_risk ?? 0) < 40).length}
          </div>
          <div className="text-sm text-muted-foreground">Low Risk</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-yellow-600">
            {students.filter((s) => (s.dropout_risk ?? 0) >= 40 && (s.dropout_risk ?? 0) < 70).length}
          </div>
          <div className="text-sm text-muted-foreground">Medium Risk</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-red-600">
            {students.filter((s) => (s.dropout_risk ?? 0) >= 70).length}
          </div>
          <div className="text-sm text-muted-foreground">High Risk</div>
        </Card>
      </div>

      {/* Students List */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">All Students</h2>
        {loading ? (
          <div className="text-center text-muted-foreground py-8">Loading...</div>
        ) : students.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            No students found
          </div>
        ) : (
          <div className="space-y-2">
            {students.map((student) => (
              <div
                key={student.id}
                className="flex items-center justify-between p-3 border rounded hover:bg-muted/50 cursor-pointer"
                onClick={() => {
                  setSelectedStudent(student);
                  loadStudentRisk(student.id);
                }}
              >
                <div>
                  <div className="font-medium">Student #{student.id}</div>
                  <div className="text-sm text-muted-foreground">
                    Last active:{" "}
                    {student.last_active
                      ? new Date(student.last_active).toLocaleDateString()
                      : "Never"}
                  </div>
                </div>
                <Badge variant={getRiskColor(student.dropout_risk) as any}>
                  {getRiskLabel(student.dropout_risk)}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Student Details Dialog */}
      {selectedStudent && (
        <Dialog open={!!selectedStudent} onOpenChange={() => setSelectedStudent(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Student #{selectedStudent.id}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-muted-foreground">Last Active</div>
                <div className="font-medium">
                  {selectedStudent.last_active
                    ? new Date(selectedStudent.last_active).toLocaleString()
                    : "Never"}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Dropout Risk</div>
                {riskDetails ? (
                  <div className="font-medium">
                    {riskDetails.risk_score.toFixed(1)}%
                  </div>
                ) : (
                  <div className="text-muted-foreground">Loading...</div>
                )}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">
                  Send Reminder
                </Button>
                <Button className="flex-1">Manual Outreach</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
