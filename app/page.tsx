"use client";

import { useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const courses = [
  {
    id: "python:pm",
    title: "Python for PM",
    description: "Learn Python programming for product management",
    level: "Beginner",
    modules: 12,
  },
  {
    id: "ai:cosmetology",
    title: "AI for Cosmetologists",
    description: "AI-powered tools and techniques for beauty industry",
    level: "Intermediate",
    modules: 8,
  },
  {
    id: "sql:basics",
    title: "SQL Basics",
    description: "Database fundamentals and SQL queries",
    level: "Beginner",
    modules: 10,
  },
  {
    id: "ai:fundamentals",
    title: "AI Fundamentals",
    description: "Introduction to artificial intelligence and machine learning",
    level: "Beginner",
    modules: 15,
  },
];

export default function HomePage() {
  const { userId, isLoaded } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoaded && !userId) {
      router.push("/sign-in");
    }
  }, [userId, isLoaded, router]);

  const selectCourse = (courseId: string) => {
    router.push(`/chat?course=${courseId}`);
  };

  if (!isLoaded || !userId) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading...
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">StudyFlow AI</h1>
        <p className="text-muted-foreground text-lg">
          Personalized AI tutor for online courses
        </p>
      </div>

      {/* Courses */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {courses.map((course) => (
          <Card
            key={course.id}
            className="p-6 flex flex-col gap-4 hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => selectCourse(course.id)}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-lg">{course.title}</h3>
                <Badge variant="outline">{course.level}</Badge>
              </div>
              <p className="text-muted-foreground text-sm">
                {course.description}
              </p>
            </div>
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>{course.modules} modules</span>
              <span>AI Tutor Ready</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="flex justify-center gap-4">
        <Button
          variant="outline"
          onClick={() => router.push("/chat")}
        >
          General Chat
        </Button>
        <Button onClick={() => router.push("/analytics")}>
          Analytics Dashboard
        </Button>
      </div>
    </div>
  );
}
