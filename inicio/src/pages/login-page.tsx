import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useFrappeAuth } from 'frappe-react-sdk'
import { EyeIcon, EyeOffIcon, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { getLoginErrorMessage } from '@/lib/auth-errors'
import { normalizeLoginUsername, validateLoginEmail, validateLoginPassword } from '@/lib/login-validation'
import { DESK_PATH, fetchPostLoginPath } from '@/lib/post-login-redirect'

type FormValues = {
  email: string
  password: string
}

async function redirectAfterLogin() {
  try {
    const path = await fetchPostLoginPath()
    window.location.assign(path)
  } catch {
    window.location.assign(DESK_PATH)
  }
}

export default function LoginPage() {
  const { login, currentUser, isLoading: authLoading, updateCurrentUser } = useFrappeAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues: { email: '', password: '' },
    mode: 'onBlur',
  })

  useEffect(() => {
    if (authLoading) return
    if (currentUser) {
      void redirectAfterLogin()
    }
  }, [authLoading, currentUser])

  const onSubmit = async (data: FormValues) => {
    const emailErr = validateLoginEmail(data.email)
    const passErr = validateLoginPassword(data.password)
    if (emailErr || passErr) {
      toast.error(emailErr ?? passErr ?? 'Datos invalidos')
      return
    }

    setSubmitting(true)
    try {
      await login({
        username: normalizeLoginUsername(data.email),
        password: data.password,
      })
      updateCurrentUser()
      toast.success('Sesion iniciada')
      await redirectAfterLogin()
    } catch (e) {
      toast.error(getLoginErrorMessage(e))
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center text-primary font-display">Barriofarma</CardTitle>
          <CardDescription className="text-center">Cerca de ti</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Correo electronico</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                placeholder="tu@barriofarma.cl"
                disabled={submitting}
                aria-invalid={errors.email ? 'true' : 'false'}
                aria-describedby={errors.email ? 'email-error' : undefined}
                {...register('email', {
                  validate: (v) => validateLoginEmail(v) ?? true,
                })}
              />
              {errors.email && (
                <p id="email-error" className="text-sm text-red-600" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Contrasena</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="********"
                  disabled={submitting}
                  className="pr-10"
                  aria-invalid={errors.password ? 'true' : 'false'}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                  {...register('password', {
                    validate: (v) => validateLoginPassword(v) ?? true,
                  })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? 'Ocultar contrasena' : 'Mostrar contrasena'}
                >
                  {showPassword ? <EyeOffIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                </button>
              </div>
              {errors.password && (
                <p id="password-error" className="text-sm text-red-600" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
                  Iniciando sesion...
                </>
              ) : (
                'Iniciar sesion'
              )}
            </Button>
            <div className="text-sm text-center text-muted-foreground">
              ¿No recuerdas tu contrasena?{' '}
              <a href="/login#forgot" className="text-primary hover:underline">
                Recuperar
              </a>
            </div>
            <div className="text-sm text-center">
              <Link to="/inicio" className="text-muted-foreground hover:text-primary">
                Volver al inicio
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
