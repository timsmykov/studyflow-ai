"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { chatStream } from "@/lib/api";
import { Message, ComplexityLevel } from "@/lib/types";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [complexity, setComplexity] = useState<ComplexityLevel>("standard");
  const [courseId, setCourseId] = useState("general");
  const [sessionId, setSessionId] = useState<number | null>(null);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now(),
      session_id: sessionId || 0,
      role: "user",
      content: input,
      tokens: 0,
      latency_ms: 0,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      let assistantContent = "";
      const assistantMessage: Message = {
        id: Date.now() + 1,
        session_id: sessionId || 0,
        role: "assistant",
        content: "",
        tokens: 0,
        latency_ms: 0,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      for await (const chunk of chatStream(sessionId, courseId, input, complexity)) {
        assistantContent += chunk;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessage.id
              ? { ...msg, content: assistantContent }
              : msg
          )
        );
      }

      setSessionId(assistantMessage.session_id);
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b px-4 py-3 flex items-center gap-3">
        <Avatar>
          <div className="w-full h-full flex items-center justify-center bg-primary text-primary-foreground">
            AI
          </div>
        </Avatar>
        <div>
          <h1 className="font-semibold">StudyFlow AI Tutor</h1>
          <p className="text-sm text-muted-foreground">
            {courseId === "general" ? "General Learning" : courseId}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Badge variant="outline" className="cursor-pointer" onClick={() => {
            const levels: ComplexityLevel[] = ["brief", "standard", "deep"];
            const currentIndex = levels.indexOf(complexity);
            setComplexity(levels[(currentIndex + 1) % 3]);
          }}>
            {complexity}
          </Badge>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4 max-w-3xl mx-auto">
          {messages.length === 0 && (
            <Card className="p-6 text-center">
              <h3 className="font-semibold mb-2">Welcome to StudyFlow!</h3>
              <p className="text-muted-foreground text-sm">
                Ask me anything about your courses. I'm here to help you learn.
              </p>
            </Card>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${
                msg.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              <Avatar className="w-8 h-8">
                <div
                  className={`w-full h-full flex items-center justify-center text-xs ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-secondary-foreground"
                  }`}
                >
                  {msg.role === "user" ? "U" : "AI"}
                </div>
              </Avatar>
              <Card
                className={`p-3 max-w-[80%] ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </Card>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4">
        <div className="max-w-3xl mx-auto flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && handleSend()}
            placeholder="Ask me anything..."
            disabled={loading}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()}>
            {loading ? "..." : "Send"}
          </Button>
        </div>
      </div>
    </div>
  );
}
