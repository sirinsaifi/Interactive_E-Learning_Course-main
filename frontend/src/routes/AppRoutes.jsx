import { Route, Routes } from "react-router-dom";

import AdminPage from "../pages/AdminPage.jsx";
import CourseDetailPage from "../pages/CourseDetailPage.jsx";
import CoursesPage from "../pages/CoursesPage.jsx";
import HealthPage from "../pages/HealthPage.jsx";
import HomePage from "../pages/HomePage.jsx";
import InstructorCourseEditorPage from "../pages/InstructorCourseEditorPage.jsx";
import InstructorPage from "../pages/InstructorPage.jsx";
import LoginPage from "../pages/LoginPage.jsx";
import NotFoundPage from "../pages/NotFoundPage.jsx";
import AdminRoute from "./AdminRoute.jsx";
import InstructorRoute from "./InstructorRoute.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/courses" element={<CoursesPage />} />
      <Route
        path="/courses/:id"
        element={
          <ProtectedRoute>
            <CourseDetailPage />
          </ProtectedRoute>
        }
      />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/instructor"
        element={
          <InstructorRoute>
            <InstructorPage />
          </InstructorRoute>
        }
      />
      <Route
        path="/instructor/courses/:id"
        element={
          <InstructorRoute>
            <InstructorCourseEditorPage />
          </InstructorRoute>
        }
      />
      <Route
        path="/health"
        element={
          <AdminRoute>
            <HealthPage />
          </AdminRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminPage />
          </AdminRoute>
        }
      />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
