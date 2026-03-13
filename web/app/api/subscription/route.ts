import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { SubscriptionPayload } from "@/lib/types";
import { SOURCES } from "@/lib/sources";

export async function POST(request: Request) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body: SubscriptionPayload = await request.json();

    // Validate channel
    if (body.channel !== "email" && body.channel !== "slack") {
      return NextResponse.json(
        { error: "Channel must be 'email' or 'slack'" },
        { status: 400 }
      );
    }

    // Validate channel-specific fields
    if (body.channel === "email") {
      if (!body.email) {
        return NextResponse.json(
          { error: "Email is required for email delivery" },
          { status: 400 }
        );
      }
    } else {
      if (
        !body.slack_webhook_url ||
        !body.slack_webhook_url.startsWith("https://hooks.slack.com/")
      ) {
        return NextResponse.json(
          { error: "A valid Slack webhook URL is required" },
          { status: 400 }
        );
      }
    }

    // Validate sources
    if (!body.source_ids || body.source_ids.length === 0) {
      return NextResponse.json(
        { error: "At least one source must be selected" },
        { status: 400 }
      );
    }

    const validIds = new Set(SOURCES.map((s) => s.id));
    const invalidIds = body.source_ids.filter((id) => !validIds.has(id));
    if (invalidIds.length > 0) {
      return NextResponse.json(
        { error: `Invalid source IDs: ${invalidIds.join(", ")}` },
        { status: 400 }
      );
    }

    // Upsert subscription
    const { error: subError } = await supabase.from("subscriptions").upsert(
      {
        user_id: user.id,
        channel: body.channel,
        email: body.channel === "email" ? body.email : null,
        slack_webhook_url:
          body.channel === "slack" ? body.slack_webhook_url : null,
        digest_time: body.digest_time,
        timezone: body.timezone,
        weekdays_only: body.weekdays_only,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "user_id" }
    );

    if (subError) {
      return NextResponse.json({ error: subError.message }, { status: 500 });
    }

    // Replace user_sources: delete existing, insert new
    const { error: deleteError } = await supabase
      .from("user_sources")
      .delete()
      .eq("user_id", user.id);

    if (deleteError) {
      return NextResponse.json(
        { error: deleteError.message },
        { status: 500 }
      );
    }

    const { error: insertError } = await supabase.from("user_sources").insert(
      body.source_ids.map((source_id) => ({
        user_id: user.id,
        source_id,
      }))
    );

    if (insertError) {
      return NextResponse.json(
        { error: insertError.message },
        { status: 500 }
      );
    }

    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json(
      { error: "Invalid request body" },
      { status: 400 }
    );
  }
}
