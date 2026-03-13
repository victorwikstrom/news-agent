"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Box, Card, Flex, Heading, Text, TextField, Button, Link } from "@radix-ui/themes";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.signUp({
      email,
      password,
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
                We sent a confirmation link to <strong>{email}</strong>. Click the link to activate your account.
              </Text>
              <Link href="/login" size="2">
                Back to login
              </Link>
            </Flex>
          ) : (
            <form onSubmit={handleSubmit}>
              <Flex direction="column" gap="4">
                <Heading size="6" align="center">
                  Create account
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
                    placeholder="Create a password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </label>

                <label>
                  <Text size="2" mb="1" weight="medium">
                    Confirm password
                  </Text>
                  <TextField.Root
                    type="password"
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </label>

                <Button type="submit" disabled={loading}>
                  {loading ? "Creating account..." : "Sign up"}
                </Button>

                <Text size="2" align="center">
                  Already have an account?{" "}
                  <Link href="/login">Log in</Link>
                </Text>
              </Flex>
            </form>
          )}
        </Card>
      </Box>
    </Flex>
  );
}
