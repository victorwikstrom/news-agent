"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Box, Card, Flex, Heading, Text, TextField, Button, Link } from "@radix-ui/themes";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/callback`,
    });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    setSuccess(true);
    setLoading(false);
  }

  return (
    <Flex align="center" justify="center" style={{ minHeight: "100vh" }}>
      <Box style={{ width: "100%", maxWidth: 400 }} px="4">
        <Card size="4">
          {success ? (
            <Flex direction="column" gap="4" align="center">
              <Heading size="6">Check your email</Heading>
              <Text size="2" align="center" color="gray">
                If an account exists for <strong>{email}</strong>, we sent a password reset link.
              </Text>
              <Link href="/login" size="2">
                Back to login
              </Link>
            </Flex>
          ) : (
            <form onSubmit={handleSubmit}>
              <Flex direction="column" gap="4">
                <Heading size="6" align="center">
                  Reset password
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

                <Button type="submit" disabled={loading}>
                  {loading ? "Sending..." : "Send reset link"}
                </Button>

                <Link href="/login" size="2" style={{ textAlign: "center" }}>
                  Back to login
                </Link>
              </Flex>
            </form>
          ) }
        </Card>
      </Box>
    </Flex>
  );
}
