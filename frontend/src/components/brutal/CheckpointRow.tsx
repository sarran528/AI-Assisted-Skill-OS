interface CheckpointRowProps {
  title: string;
  status: "pending" | "attempted" | "passed" | "failed";
}

export function CheckpointRow({ title, status }: CheckpointRowProps) {
  return (
    <div className="checkpoint-row">
      <span>{title}</span>
      <span className={`status-pill status-pill--${status}`}>{status.toUpperCase()}</span>
    </div>
  );
}
