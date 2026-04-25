import { useState } from "react";
import { useUploadEvidence } from "../../hooks/useSession";

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "application/pdf", "text/plain", "video/mp4"];

export function EvidenceUploader({ sessionId, checkpointId }: { sessionId: string; checkpointId: string }) {
  const [error, setError] = useState<string | null>(null);
  const { mutate: uploadEvidence, isPending } = useUploadEvidence();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > MAX_FILE_SIZE) {
        setError("File exceeds 50MB limit");
        return;
      }
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        setError("Invalid file type");
        return;
      }
      setError(null);
      uploadEvidence({ sessionId, checkpointId, file });
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} disabled={isPending} />
      {error && <p style={{ color: "red" }}>{error}</p>}
      {isPending && <p>Uploading...</p>}
    </div>
  );
}
