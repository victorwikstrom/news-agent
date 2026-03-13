"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Box, Card, Flex, Heading, Text, TextField, Button, Link } from "@radix-ui/themes";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    router.push("/dashboard");
    router.refresh();
  }

  return (
    <Flex align="center" justify="center" style={{ minHeight: "100vh" }}>
      <Box style={{ width: "100%", maxWidth: 400 }} px="4">
        <Card size="4">
          <form onSubmit={handleSubmit}>
            <Flex direction="column" gap="4">
              <Heading size="6" align="center">
                Log in
              </Heading>

              {error && (
                <Text color="red" size="2" align="center">
                  {error}
                </Text>
              )}

              <label>
                <Text size="2" mb="1" weight="medium">
                  Email
                </Text>
                <TextField.Root
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </label>

              <label>
                <Text size="2" mb="1" weight="medium">
                  Password
                </Text>
                <TextField.Root
                  type="password"
                  placeholder="Your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </label>

              <Button type="submit" disabled={loading}>
                {loading ? "Signing in..." : "Sign in"}
              </Button>

              <Flex justify="between">
                <Link href="/signup" size="2">
                  Create an account
                </Link>
                <Link href="/forgot-password" size="2">
                  Forgot password?
                </Link>
              </Flex>
            </Flex>
          </form>
        </Card>
      </Box>
    </Flex>
  );
}
