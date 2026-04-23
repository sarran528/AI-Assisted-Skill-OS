import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { loginUser } from "../api/auth";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useAuthStore } from "../store/authStore";
import axiosClient from "../api/axiosClient";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string()
    .min(8, "Password must be at least 8 characters long")
    .max(72, "Password cannot exceed 72 characters")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[a-z]/, "Password must contain at least one lowercase letter")
    .regex(/\d/, "Password must contain at least one digit")
    .regex(/[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/\?]/, "Password must contain at least one special character")
    .refine((password) => !['password', '12345678', 'qwerty123', 'admin123'].includes(password.toLowerCase()), 
            "Password is too common and easily guessable"),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginView() {
  const navigate = useNavigate();
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);

  const { register, handleSubmit, formState } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data: any) => {
      const token = data.accessToken || data.access_token;
      setToken(token);
      
      // Make authenticated request with explicit token
      axiosClient
        .get("/users/me", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
        .then((res) => setUser({ id: res.data.id, email: res.data.email }))
        .catch((error) => {
          console.error("Failed to fetch user data:", error);
          setUser(null);
        })
        .finally(() => navigate("/dashboard"));
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
            maxLength={72}
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
