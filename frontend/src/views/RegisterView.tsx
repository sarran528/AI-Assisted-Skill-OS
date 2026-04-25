import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { registerUser } from "../api/auth";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useAuthStore } from "../store/authStore";

const registerSchema = z.object({
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

type RegisterForm = z.infer<typeof registerSchema>;

export function RegisterView() {
  const navigate = useNavigate();
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);

  const { register, handleSubmit, formState } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "" },
  });

  const registerMutation = useMutation({
    mutationFn: registerUser,
    onSuccess: (data: any) => {
      const token = data.accessToken || data.access_token;
      setToken(token);
      setUser({ id: data.user_id, email: data.email ?? "" });
      navigate("/dashboard");
    },
  });

  return (
    <main className="auth-layout">
      <BrutalCard accent="yellow" className="auth-card">
        <h1 className="headline">Create SkillOS Account</h1>
        <form className="auth-form" onSubmit={handleSubmit((payload) => registerMutation.mutate(payload))}>
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
          {formState.errors.password && <p className="error-text">{formState.errors.password.message}</p>}
          {registerMutation.isError && <p className="error-text">Registration failed.</p>}

          <BrutalButton data-testid="register-btn" type="submit" variant="primary" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? "Creating..." : "Register"}
          </BrutalButton>
        </form>
        <p className="auth-link-row">
          Already registered? <Link to="/login">Login</Link>
        </p>
      </BrutalCard>
    </main>
  );
}
