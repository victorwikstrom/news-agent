"use client";

import { useState } from "react";
import {
  Box,
  Button,
  Card,
  Flex,
  Heading,
  Switch,
  Text,
  TextField,
} from "@radix-ui/themes";
import { SOURCES, CATEGORIES } from "@/lib/sources";
import { Channel, Subscription, SubscriptionPayload } from "@/lib/types";

type Props = {
  userEmail: string;
  initialSubscription: Subscription | null;
  initialSourceIds: string[];
};

export default function DashboardForm({
  userEmail,
  initialSubscription,
  initialSourceIds,
}: Props) {
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>(
    initialSourceIds
  );
  const [channel, setChannel] = useState<Channel>(
    initialSubscription?.channel ?? "email"
  );
  const [email, setEmail] = useState(
    initialSubscription?.email ?? userEmail
  );
  const [slackWebhookUrl, setSlackWebhookUrl] = useState(
    initialSubscription?.slack_webhook_url ?? ""
  );
  const [digestTime, setDigestTime] = useState(
    initialSubscription?.digest_time ?? "07:00"
  );
  const [weekdaysOnly, setWeekdaysOnly] = useState(
    initialSubscription?.weekdays_only ?? true
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function toggleSource(id: string) {
    setSelectedSourceIds((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  }

  function validate(): string | null {
    if (selectedSourceIds.length === 0) {
      return "Select at least one news source.";
    }
    if (channel === "email" && !email) {
      return "Email address is required.";
    }
    if (
      channel === "slack" &&
      (!slackWebhookUrl ||
        !slackWebhookUrl.startsWith("https://hooks.slack.com/"))
    ) {
      return "A valid Slack webhook URL is required (must start with https://hooks.slack.com/).";
    }
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);

    const payload: SubscriptionPayload = {
      channel,
      digest_time: digestTime,
      timezone: "Europe/Stockholm",
      weekdays_only: weekdaysOnly,
      source_ids: selectedSourceIds,
      ...(channel === "email" ? { email } : { slack_webhook_url: slackWebhookUrl }),
    };

    try {
      const res = await fetch("/api/subscription", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? "Something went wrong.");
        setSaving(false);
        return;
      }

      setSaved(true);
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  if (saved) {
    return (
      <Card size="4">
        <Flex direction="column" gap="4" align="center" py="6">
          <Heading size="5">Settings saved</Heading>
          <Text size="2" color="gray" align="center">
            Your news digest is configured. You&apos;ll receive your first
            digest at {digestTime} (Europe/Stockholm).
          </Text>
          <Button variant="outline" onClick={() => setSaved(false)}>
            Edit settings
          </Button>
        </Flex>
      </Card>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <Flex direction="column" gap="6">
        {/* Section A — Source Picker */}
        <Card size="3">
          <Flex direction="column" gap="4">
            <Heading size="4">News Sources</Heading>
            <Text size="2" color="gray">
              Pick the sources you want included in your digest.
            </Text>

            {CATEGORIES.map((category) => (
              <Flex direction="column" gap="2" key={category}>
                <Text size="2" weight="medium">
                  {category}
                </Text>
                <Flex gap="2" wrap="wrap">
                  {SOURCES.filter((s) => s.category === category).map(
                    (source) => {
                      const selected = selectedSourceIds.includes(source.id);
                      return (
                        <Box
                          key={source.id}
                          onClick={() => toggleSource(source.id)}
                          style={{
                            padding: "8px 16px",
                            borderRadius: "var(--radius-2)",
                            border: selected
                              ? "2px solid var(--accent-9)"
                              : "2px solid var(--gray-6)",
                            background: selected
                              ? "var(--accent-3)"
                              : "transparent",
                            cursor: "pointer",
                            userSelect: "none",
                          }}
                        >
                          <Text size="2" weight={selected ? "bold" : "regular"}>
                            {source.name}
                          </Text>
                        </Box>
                      );
                    }
                  )}
                </Flex>
              </Flex>
            ))}
          </Flex>
        </Card>

        {/* Section B — Delivery Channel */}
        <Card size="3">
          <Flex direction="column" gap="4">
            <Heading size="4">Delivery Channel</Heading>
            <Text size="2" color="gray">
              Choose how you want to receive your digest.
            </Text>

            <Flex gap="2">
              <Button
                type="button"
                variant={channel === "email" ? "solid" : "outline"}
                onClick={() => setChannel("email")}
              >
                Email
              </Button>
              <Button
                type="button"
                variant={channel === "slack" ? "solid" : "outline"}
                onClick={() => setChannel("slack")}
              >
                Slack
              </Button>
            </Flex>

            {channel === "email" && (
              <label>
                <Text size="2" mb="1" weight="medium">
                  Email address
                </Text>
                <TextField.Root
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </label>
            )}

            {channel === "slack" && (
              <label>
                <Text size="2" mb="1" weight="medium">
                  Slack webhook URL
                </Text>
                <TextField.Root
                  type="url"
                  placeholder="https://hooks.slack.com/services/..."
                  value={slackWebhookUrl}
                  onChange={(e) => setSlackWebhookUrl(e.target.value)}
                  required
                />
                <Text size="1" color="gray" mt="1">
                  Create an incoming webhook in your Slack workspace settings.
                </Text>
              </label>
            )}
          </Flex>
        </Card>

        {/* Section C — Schedule */}
        <Card size="3">
          <Flex direction="column" gap="4">
            <Heading size="4">Schedule</Heading>
            <Text size="2" color="gray">
              When should we send your digest?
            </Text>

            <label>
              <Text size="2" mb="1" weight="medium">
                Delivery time
              </Text>
              <TextField.Root
                type="time"
                value={digestTime}
                onChange={(e) => setDigestTime(e.target.value)}
                required
              />
              <Text size="1" color="gray" mt="1">
                Timezone: Europe/Stockholm
              </Text>
            </label>

            <Flex align="center" gap="2">
              <Switch
                checked={weekdaysOnly}
                onCheckedChange={(checked) => setWeekdaysOnly(checked)}
              />
              <Text size="2">Weekdays only (Mon–Fri)</Text>
            </Flex>
          </Flex>
        </Card>

        {/* Error message */}
        {error && (
          <Text color="red" size="2">
            {error}
          </Text>
        )}

        {/* Submit */}
        <Button type="submit" size="3" disabled={saving}>
          {saving ? "Saving..." : "Save settings"}
        </Button>
      </Flex>
    </form>
  );
}
