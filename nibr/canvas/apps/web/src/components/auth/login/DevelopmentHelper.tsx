"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Copy, User, Shield } from "lucide-react";

interface TestAccount {
  username: string;
  password: string;
  isAdmin: boolean;
}

interface DevelopmentHelperProps {
  onQuickLogin?: (username: string, password: string) => void;
}

export function DevelopmentHelper({ onQuickLogin }: DevelopmentHelperProps) {
  const [testAccounts, setTestAccounts] = useState<TestAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Only show in development
    if (process.env.NODE_ENV !== 'development') {
      setIsLoading(false);
      return;
    }

    // Fetch test accounts
    fetch('/api/auth/test-accounts')
      .then(res => res.json())
      .then(data => {
        if (data.accounts) {
          setTestAccounts(data.accounts);
        }
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleQuickLogin = (username: string, password: string) => {
    if (onQuickLogin) {
      onQuickLogin(username, password);
    }
  };

  // Don't show in production
  if (process.env.NODE_ENV !== 'development' || isLoading) {
    return null;
  }

  return (
    <Card className="mt-6 border-orange-200 bg-orange-50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm text-orange-800 flex items-center gap-2">
          <span className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></span>
          Development Mode
        </CardTitle>
        <CardDescription className="text-orange-700">
          Quick login with test accounts
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {testAccounts.map((account) => (
          <div key={account.username} className="flex items-center justify-between p-2 bg-white rounded border">
            <div className="flex items-center gap-2">
              {account.isAdmin ? (
                <Shield className="w-4 h-4 text-red-500" />
              ) : (
                <User className="w-4 h-4 text-blue-500" />
              )}
              <div className="text-sm">
                <div className="font-medium">{account.username}</div>
                <div className="text-gray-500 text-xs">Password: {account.password}</div>
              </div>
              {account.isAdmin && (
                <Badge variant="destructive" className="text-xs">Admin</Badge>
              )}
            </div>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(`${account.username}:${account.password}`)}
                className="p-1 h-6 w-6"
              >
                <Copy className="w-3 h-3" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleQuickLogin(account.username, account.password)}
                className="text-xs px-2 py-1 h-6"
              >
                Login
              </Button>
            </div>
          </div>
        ))}
        <div className="pt-2 border-t border-orange-200">
          <p className="text-xs text-orange-600">
            💡 You can also create new accounts using the Sign Up button
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
