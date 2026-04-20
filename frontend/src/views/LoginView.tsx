import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { loginUser } from "../api/auth";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useAuthStore } from "../store/authStore";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginView() {
  const navigate = useNavigate();
  const setToken = useAuthStore((state) => state.setToken);

  const { register, handleSubmit, formState } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data) => {
      setToken(data.access_token);
      navigate("/dashboard");
    },
  });

  return (
    <main className="auth-layout">
      <BrutalCard className="auth-card">
        <h1 className="headline">SkillOS Login</h1>
        <form className="auth-form" onSubmit={handleSubmit((payload) => loginMutation.mutate(payload))}>
          <label htmlFor="email">Email</label>
          <input id="email" data-testid="email" className="brutal-input" type="email" {...register("email")} />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            data-testid="password"
            className="brutal-input"
            type="password"
            {...register("password")}
          />

          {formState.errors.email && <p className="error-text">Valid email is required.</p>}
          {formState.errors.password && <p className="error-text">Password must be at least 8 chars.</p>}
          {loginMutation.isError && <p className="error-text">Login failed.</p>}

          <BrutalButton data-testid="login-btn" type="submit" variant="primary" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Signing in..." : "Login"}
          </BrutalButton>
        </form>
        <p className="auth-link-row">
          Need an account? <Link to="/register">Register</Link>
        </p>
      </BrutalCard>
    </main>
  );
}
