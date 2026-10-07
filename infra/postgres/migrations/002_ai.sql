CREATE TABLE IF NOT EXISTS content_chunks(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 source_type text NOT NULL,
 source_id uuid NOT NULL,
 chunk_index int NOT NULL,
 content text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS embeddings(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 source_type text NOT NULL,
 source_id uuid NOT NULL,
 chunk_id uuid REFERENCES content_chunks(id) ON DELETE CASCADE,
 model_name text NOT NULL,
 embedding vector(1024),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_conversations(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 title text,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_messages(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 conversation_id uuid REFERENCES ai_conversations(id) ON DELETE CASCADE,
 role text NOT NULL,
 content text NOT NULL,
 model text,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_actions(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 conversation_id uuid REFERENCES ai_conversations(id) ON DELETE SET NULL,
 action_type text NOT NULL,
 title text NOT NULL,
 payload jsonb NOT NULL DEFAULT '{}'::jsonb,
 status text NOT NULL DEFAULT 'proposed',
 expires_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS audit_logs(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 event_type text NOT NULL,
 entity_type text NOT NULL,
 entity_id uuid,
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now()
);
