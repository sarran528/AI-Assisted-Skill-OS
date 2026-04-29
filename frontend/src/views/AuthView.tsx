import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import axiosClient from "../api/axiosClient";
import { loginUser, registerUser } from "../api/auth";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useAuthStore } from "../store/authStore";
import { useAssessmentStore } from "../stores/assessmentStore";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8, "Password must be at least 8 characters."),
});

const registerSchema = loginSchema.extend({
  confirmPassword: z.string().min(8, "Confirm password is required."),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match.",
  path: ["confirmPassword"],
});

type LoginForm = z.infer<typeof loginSchema>;
type RegisterForm = z.infer<typeof registerSchema>;

export function AuthView({ defaultMode = "login" }: { defaultMode?: "login" | "register" }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">(defaultMode);
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);
  const resetAssessment = useAssessmentStore((state) => state.resetAssessment);

  const loginForm = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });
  const registerForm = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "", confirmPassword: "" },
  });

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data: any) => {
      const token = data.accessToken || data.access_token;
      // Session ids are user-scoped; clear persisted assessment state on auth change.
      resetAssessment();
      setToken(token);
      axiosClient
        .get("/users/me", { headers: { Authorization: `Bearer ${token}` } })
        .then((res) => setUser({ id: res.data.id, email: res.data.email }))
        .finally(() => navigate("/dashboard"));
    },
  });

  const registerMutation = useMutation({
    mutationFn: registerUser,
    onSuccess: (data: any) => {
      const token = data.accessToken || data.access_token;
      // New account should always start with a fresh assessment session state.
      resetAssessment();
      setToken(token);
      setUser({ id: data.user_id, email: data.email ?? "" });
      navigate("/dashboard");
    },
  });

  return (
    <main className="auth-layout">
      <BrutalCard className="auth-card">
        <h1 className="headline" style={{ textAlign: "center", marginBottom: "1rem" }}>SkillOS</h1>

        {mode === "login" ? (
          <form className="auth-form" onSubmit={loginForm.handleSubmit((payload) => loginMutation.mutate(payload))}>
            <label htmlFor="email">Email</label>
            <input id="email" className="brutal-input" type="email" {...loginForm.register("email")} />
            <label htmlFor="password">Password</label>
            <input id="password" className="brutal-input" type="password" {...loginForm.register("password")} />
            {loginForm.formState.errors.email && <p className="error-text">Valid email is required.</p>}
            {loginForm.formState.errors.password && <p className="error-text">{loginForm.formState.errors.password.message}</p>}
            {loginMutation.isError && <p className="error-text">Login failed.</p>}
            <BrutalButton type="submit" variant="primary" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? "Signing in..." : "Login"}
            </BrutalButton>
          </form>
        ) : (
          <form className="auth-form" onSubmit={registerForm.handleSubmit((payload) => registerMutation.mutate(payload))}>
            <label htmlFor="register-email">Email</label>
            <input id="register-email" className="brutal-input" type="email" {...registerForm.register("email")} />
            <label htmlFor="register-password">Password</label>
            <input id="register-password" className="brutal-input" type="password" {...registerForm.register("password")} />
            <label htmlFor="confirm-password">Confirm Password</label>
            <input id="confirm-password" className="brutal-input" type="password" {...registerForm.register("confirmPassword")} />
            {registerForm.formState.errors.email && <p className="error-text">Valid email is required.</p>}
            {registerForm.formState.errors.password && <p className="error-text">{registerForm.formState.errors.password.message}</p>}
            {registerForm.formState.errors.confirmPassword && <p className="error-text">{registerForm.formState.errors.confirmPassword.message}</p>}
            {registerMutation.isError && <p className="error-text">Registration failed.</p>}
            <BrutalButton type="submit" variant="primary" disabled={registerMutation.isPending}>
              {registerMutation.isPending ? "Creating..." : "Register"}
            </BrutalButton>
          </form>
        )}

        <p className="auth-link-row" style={{ textAlign: "center", marginTop: "1rem" }}>
          {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
          <button
            type="button"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
            style={{ border: "none", background: "transparent", textDecoration: "underline", cursor: "pointer" }}
          >
            {mode === "login" ? "Register" : "Login"}
          </button>
        </p>
      </BrutalCard>
    </main>
  );
}
